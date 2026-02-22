import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.clients.radarr import get_radarr
from bot.clients.sonarr import get_sonarr
from bot.formatting import format_search_result
from bot.keyboards import (
    BTN_CANCEL,
    BTN_SEARCH_MOVIES,
    BTN_SEARCH_SHOWS,
    main_menu_keyboard,
    quality_profile_keyboard,
    root_folder_keyboard,
    search_input_keyboard,
    search_results_keyboard,
    search_type_keyboard,
    season_select_keyboard,
)
from bot.middleware import whitelist_only

logger = logging.getLogger(__name__)

CHOOSE_TYPE, TYPE_QUERY = range(2)


@whitelist_only
async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info("User %s (%s) → 🔍 Search", user.full_name, user.id)
    await update.message.reply_text(
        "🔍 What do you want to search for?",
        reply_markup=search_type_keyboard(),
    )
    return CHOOSE_TYPE


@whitelist_only
async def search_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    text = update.message.text
    if text == BTN_SEARCH_MOVIES:
        context.user_data["search_type"] = "m"
        label = "movie"
        logger.info("User %s (%s) → Search type: 🎬 Movies", user.full_name, user.id)
    else:
        context.user_data["search_type"] = "s"
        label = "TV show"
        logger.info("User %s (%s) → Search type: 📺 TV Shows", user.full_name, user.id)
    await update.message.reply_text(
        f"✏️ Enter the {label} name to search:",
        reply_markup=search_input_keyboard(),
    )
    return TYPE_QUERY


@whitelist_only
async def search_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info("User %s (%s) → ❌ Search cancelled", user.full_name, user.id)
    await update.message.reply_text("❌ Search cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


@whitelist_only
async def search_query_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    media_type = context.user_data.get("search_type", "m")
    term = update.message.text.strip()
    if not term or len(term) > 200:
        await update.message.reply_text(
            "⚠️ Please enter a search term between 1 and 200 characters.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    type_label = "🎬 movie" if media_type == "m" else "📺 TV show"
    logger.info("User %s (%s) → Search %s: '%s'", user.full_name, user.id, type_label, term)

    if media_type == "m":
        results = await get_radarr().lookup(term)
        existing = await get_radarr().get_movies()
        existing_ids = {m["tmdbId"] for m in existing}
    else:
        results = await get_sonarr().lookup(term)
        existing = await get_sonarr().get_series()
        existing_ids = {s["tvdbId"] for s in existing}

    logger.info("Search returned %d results", len(results))

    if not results:
        await update.message.reply_text(
            "😔 No results found. Use /search to try again.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    # Cache results for the add handler
    id_key = "tmdbId" if media_type == "m" else "tvdbId"
    context.user_data["search_results"] = {
        item[id_key]: item for item in results[:10] if id_key in item
    }

    # Build text with descriptions
    lines = [f"🔎 Found {len(results)} result(s):\n"]
    for i, item in enumerate(results[:10], 1):
        lines.append(f"{i}. {format_search_result(item, media_type)}\n")
    text = "\n".join(lines)

    kb = search_results_keyboard(results, media_type, existing_ids)
    await update.message.reply_text(
        "🔎 Searching...",
        reply_markup=main_menu_keyboard(),
    )
    await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")
    return ConversationHandler.END


@whitelist_only
async def add_from_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped '+' on a search result — show quality profile picker."""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")
    media_type = parts[1]
    item_id = int(parts[2])

    cached = context.user_data.get("search_results", {})
    item = cached.get(item_id)
    if not item:
        await query.answer("⏳ Result expired. Please search again.", show_alert=True)
        return

    title = item.get("title", "Unknown")
    logger.info("User %s (%s) → ➕ Add '%s' (picking quality profile)", user.full_name, user.id, title)

    try:
        if media_type == "m":
            profiles = await get_radarr().get_quality_profiles()
        else:
            profiles = await get_sonarr().get_quality_profiles()
    except Exception:
        logger.exception("Failed to load quality profiles")
        await query.answer("⚠️ Failed to load profiles.", show_alert=True)
        return

    await query.answer()
    await query.edit_message_text(
        f"🎯 Select quality profile for <b>{title}</b>:",
        reply_markup=quality_profile_keyboard(profiles, media_type, item_id),
        parse_mode="HTML",
    )


@whitelist_only
async def quality_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User picked a quality profile — show root folder picker."""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")
    media_type = parts[1]
    item_id = int(parts[2])
    profile_id = int(parts[3])

    cached = context.user_data.get("search_results", {})
    item = cached.get(item_id)
    if not item:
        await query.answer("⏳ Result expired. Please search again.", show_alert=True)
        return

    title = item.get("title", "Unknown")
    context.user_data["add_quality_profile_id"] = profile_id
    logger.info("User %s (%s) → 🎯 Quality profile %d for '%s' (picking root folder)", user.full_name, user.id, profile_id, title)

    try:
        if media_type == "m":
            folders = await get_radarr().get_root_folders()
        else:
            folders = await get_sonarr().get_root_folders()
    except Exception:
        logger.exception("Failed to load root folders")
        await query.answer("⚠️ Failed to load folders.", show_alert=True)
        return

    await query.answer()
    await query.edit_message_text(
        f"📁 Select root folder for <b>{title}</b>:",
        reply_markup=root_folder_keyboard(folders, media_type, item_id),
        parse_mode="HTML",
    )


@whitelist_only
async def confirm_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User picked a root folder — add movie or show season picker."""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")
    media_type = parts[1]
    item_id = int(parts[2])
    folder_id = int(parts[3])

    cached = context.user_data.get("search_results", {})
    item = cached.get(item_id)
    if not item:
        await query.answer("⏳ Result expired. Please search again.", show_alert=True)
        return

    profile_id = context.user_data.get("add_quality_profile_id")
    if not profile_id:
        await query.answer("⏳ Session expired. Please search again.", show_alert=True)
        return

    title = item.get("title", "Unknown")

    try:
        if media_type == "m":
            folders = await get_radarr().get_root_folders()
        else:
            folders = await get_sonarr().get_root_folders()
        folder = next((f for f in folders if f["id"] == folder_id), None)
        if not folder:
            await query.answer("⚠️ Root folder not found.", show_alert=True)
            return
        root_path = folder["path"]
        context.user_data["add_root_folder_path"] = root_path
    except Exception:
        logger.exception("Failed to load root folders")
        await query.answer("⚠️ Failed to load folders.", show_alert=True)
        return

    if media_type == "m":
        # Movies — add directly
        try:
            logger.info("User %s (%s) → ✅ Adding movie '%s' (profile=%d, folder='%s')", user.full_name, user.id, title, profile_id, root_path)
            await get_radarr().add_movie(item, profile_id, root_path)
            await query.answer(f"✅ Added: {title}", show_alert=True)
            await query.edit_message_text(f"✅ Added <b>{title}</b> to library!", parse_mode="HTML")
        except Exception:
            logger.exception("Failed to add movie '%s'", title)
            await query.answer("⚠️ Failed to add movie.", show_alert=True)
    else:
        # TV Shows — season selection step
        seasons = item.get("seasons", [])
        context.user_data["add_seasons"] = {
            s["seasonNumber"]: s.get("monitored", True) for s in seasons
        }
        logger.info("User %s (%s) → 📂 Picking seasons for '%s'", user.full_name, user.id, title)
        await query.answer()
        await query.edit_message_text(
            f"📂 Select seasons to monitor for <b>{title}</b>:",
            reply_markup=season_select_keyboard(item_id, seasons),
            parse_mode="HTML",
        )


@whitelist_only
async def toggle_season(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a season's monitoring status during add flow."""
    query = update.callback_query
    parts = query.data.split(":")
    tvdb_id = int(parts[1])
    season_num = int(parts[2])

    add_seasons = context.user_data.get("add_seasons", {})
    add_seasons[season_num] = not add_seasons.get(season_num, True)
    context.user_data["add_seasons"] = add_seasons

    cached = context.user_data.get("search_results", {})
    item = cached.get(tvdb_id)
    if not item:
        await query.answer("⏳ Result expired.", show_alert=True)
        return

    # Rebuild seasons list with updated monitoring
    seasons = []
    for s in item.get("seasons", []):
        sn = s["seasonNumber"]
        seasons.append({"seasonNumber": sn, "monitored": add_seasons.get(sn, True)})

    title = item.get("title", "Unknown")
    await query.answer()
    await query.edit_message_reply_markup(
        reply_markup=season_select_keyboard(tvdb_id, seasons),
    )


@whitelist_only
async def final_add_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm and add TV show with selected season monitoring."""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")
    tvdb_id = int(parts[1])

    cached = context.user_data.get("search_results", {})
    item = cached.get(tvdb_id)
    if not item:
        await query.answer("⏳ Result expired. Please search again.", show_alert=True)
        return

    profile_id = context.user_data.get("add_quality_profile_id")
    root_path = context.user_data.get("add_root_folder_path")
    if not profile_id or not root_path:
        await query.answer("⏳ Session expired. Please search again.", show_alert=True)
        return

    title = item.get("title", "Unknown")
    add_seasons = context.user_data.get("add_seasons", {})

    # Apply season monitoring choices to the item
    for s in item.get("seasons", []):
        sn = s["seasonNumber"]
        s["monitored"] = add_seasons.get(sn, True)

    try:
        logger.info(
            "User %s (%s) → ✅ Adding show '%s' (profile=%d, folder='%s', seasons=%s)",
            user.full_name, user.id, title, profile_id, root_path, add_seasons,
        )
        await get_sonarr().add_series(item, profile_id, root_path)
        await query.answer(f"✅ Added: {title}", show_alert=True)
        await query.edit_message_text(f"✅ Added <b>{title}</b> to library!", parse_mode="HTML")
    except Exception:
        logger.exception("Failed to add show '%s'", title)
        await query.answer("⚠️ Failed to add show.", show_alert=True)
