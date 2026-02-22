import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.callbacks import parse_callback
from bot.clients.sonarr import get_sonarr
from bot.formatting import (
    format_season_detail,
    format_season_list,
    format_show_detail,
    format_show_list_item,
)
from bot.keyboards import (
    delete_confirm_keyboard,
    paginated_list,
    season_detail_keyboard,
    season_list_keyboard,
    show_detail_keyboard,
)
from bot.middleware import whitelist_only

logger = logging.getLogger(__name__)


async def _get_sorted_shows() -> list[dict]:
    shows = await get_sonarr().get_series()
    shows.sort(key=lambda s: s.get("sortTitle", s.get("title", "")).lower())
    return shows


@whitelist_only
async def shows_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info("User %s (%s) → 📺 Shows list", user.full_name, user.id)
    shows = await _get_sorted_shows()
    if not shows:
        await update.message.reply_text("📺 No shows in library.")
        return
    context.user_data["shows_cache"] = shows
    text, kb = paginated_list(shows, 0, "s", format_show_list_item)
    await update.message.reply_text(text, reply_markup=kb)


@whitelist_only
async def show_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, page_str = parse_callback(query.data)
    logger.info("User %s (%s) → 📺 Shows page %s", update.effective_user.full_name, update.effective_user.id, page_str)
    shows = context.user_data.get("shows_cache") or await _get_sorted_shows()
    context.user_data["shows_cache"] = shows
    text, kb = paginated_list(shows, int(page_str), "s", format_show_list_item)
    await query.edit_message_text(text, reply_markup=kb)


@whitelist_only
async def show_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, show_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 📺 Show detail #%s", update.effective_user.full_name, update.effective_user.id, show_id_str)
    show = await get_sonarr().get_show(int(show_id_str))
    text = format_show_detail(show)
    await query.edit_message_text(text, reply_markup=show_detail_keyboard(show), parse_mode="HTML")


@whitelist_only
async def show_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, show_id_str = parse_callback(query.data)
    show = await get_sonarr().get_show(int(show_id_str))
    show["monitored"] = not show["monitored"]
    show = await get_sonarr().update_series(show)
    state = "📡 monitored" if show["monitored"] else "📴 unmonitored"
    logger.info("User %s (%s) → 📺 Show '%s' → %s", update.effective_user.full_name, update.effective_user.id, show["title"], state)
    await query.answer(f"Show {state}.")
    context.user_data.pop("shows_cache", None)
    text = format_show_detail(show)
    await query.edit_message_text(text, reply_markup=show_detail_keyboard(show), parse_mode="HTML")


@whitelist_only
async def show_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, show_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🔍 Search show #%s", update.effective_user.full_name, update.effective_user.id, show_id_str)
    await get_sonarr().search_series(int(show_id_str))
    await query.answer("🔍 Search triggered!", show_alert=True)


@whitelist_only
async def show_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, show_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🗑 Delete show #%s (confirming)", update.effective_user.full_name, update.effective_user.id, show_id_str)
    await query.edit_message_text(
        "⚠️ Are you sure you want to delete this show?",
        reply_markup=delete_confirm_keyboard("s", int(show_id_str)),
    )


@whitelist_only
async def show_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, show_id_str, delete_files_str = parse_callback(query.data)
    delete_files = delete_files_str == "1"
    logger.info("User %s (%s) → 🗑 Confirmed delete show #%s (files=%s)", update.effective_user.full_name, update.effective_user.id, show_id_str, delete_files)
    await get_sonarr().delete_series(int(show_id_str), delete_files=delete_files)
    context.user_data.pop("shows_cache", None)
    action = "🗑 Deleted with files removed" if delete_files else "🗑 Deleted (files kept)"
    await query.answer(f"{action}.", show_alert=True)
    await query.edit_message_text(f"{action}.")


@whitelist_only
async def show_seasons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, show_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 📂 Seasons for show #%s", update.effective_user.full_name, update.effective_user.id, show_id_str)
    show = await get_sonarr().get_show(int(show_id_str))
    episodes = await get_sonarr().get_episodes(int(show_id_str))
    text = format_season_list(show, episodes)
    await query.edit_message_text(text, reply_markup=season_list_keyboard(show), parse_mode="HTML")


@whitelist_only
async def show_season_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, show_id_str, season_str = parse_callback(query.data)
    show_id = int(show_id_str)
    season_number = int(season_str)
    logger.info("User %s (%s) → 📂 Season %s detail for show #%s", update.effective_user.full_name, update.effective_user.id, season_str, show_id_str)
    show = await get_sonarr().get_show(show_id)
    episodes = await get_sonarr().get_episodes(show_id)
    season = next(
        (s for s in show.get("seasons", []) if s["seasonNumber"] == season_number),
        {},
    )
    text = format_season_detail(show, season_number, episodes)
    await query.edit_message_text(
        text,
        reply_markup=season_detail_keyboard(show_id, season_number, season.get("monitored", False)),
        parse_mode="HTML",
    )


@whitelist_only
async def show_season_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, show_id_str, season_str = parse_callback(query.data)
    show_id = int(show_id_str)
    season_number = int(season_str)
    show = await get_sonarr().get_show(show_id)
    for season in show.get("seasons", []):
        if season["seasonNumber"] == season_number:
            season["monitored"] = not season["monitored"]
            break
    show = await get_sonarr().update_series(show)
    season = next(
        (s for s in show.get("seasons", []) if s["seasonNumber"] == season_number),
        {},
    )
    state = "📡 monitored" if season.get("monitored") else "📴 unmonitored"
    logger.info("User %s (%s) → 📂 Season %s → %s", update.effective_user.full_name, update.effective_user.id, season_str, state)
    await query.answer(f"Season {state}.")
    episodes = await get_sonarr().get_episodes(show_id)
    text = format_season_detail(show, season_number, episodes)
    await query.edit_message_text(
        text,
        reply_markup=season_detail_keyboard(show_id, season_number, season.get("monitored", False)),
        parse_mode="HTML",
    )


@whitelist_only
async def show_season_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, show_id_str, season_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🔍 Search season %s for show #%s", update.effective_user.full_name, update.effective_user.id, season_str, show_id_str)
    await get_sonarr().search_season(int(show_id_str), int(season_str))
    await query.answer("🔍 Season search triggered!", show_alert=True)


@whitelist_only
async def show_back_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    logger.info("User %s (%s) → ⬅️ Back to shows list", update.effective_user.full_name, update.effective_user.id)
    shows = await _get_sorted_shows()
    context.user_data["shows_cache"] = shows
    if not shows:
        await query.edit_message_text("📺 No shows in library.")
        return
    text, kb = paginated_list(shows, 0, "s", format_show_list_item)
    await query.edit_message_text(text, reply_markup=kb)


@whitelist_only
async def show_back_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, show_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → ⬅️ Back to show #%s detail", update.effective_user.full_name, update.effective_user.id, show_id_str)
    show = await get_sonarr().get_show(int(show_id_str))
    text = format_show_detail(show)
    await query.edit_message_text(text, reply_markup=show_detail_keyboard(show), parse_mode="HTML")
