import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.callbacks import parse_callback
from bot.clients.radarr import get_radarr
from bot.formatting import format_movie_detail, format_movie_list_item
from bot.keyboards import (
    delete_confirm_keyboard,
    movie_detail_keyboard,
    paginated_list,
)
from bot.middleware import whitelist_only

logger = logging.getLogger(__name__)


async def _get_sorted_movies() -> list[dict]:
    movies = await get_radarr().get_movies()
    movies.sort(key=lambda m: m.get("sortTitle", m.get("title", "")).lower())
    return movies


@whitelist_only
async def movies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info("User %s (%s) → 🎬 Movies list", user.full_name, user.id)
    movies = await _get_sorted_movies()
    if not movies:
        await update.message.reply_text("🎬 No movies in library.")
        return
    context.user_data["movies_cache"] = movies
    text, kb = paginated_list(movies, 0, "m", format_movie_list_item)
    await update.message.reply_text(text, reply_markup=kb)


@whitelist_only
async def movie_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, page_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🎬 Movies page %s", update.effective_user.full_name, update.effective_user.id, page_str)
    movies = context.user_data.get("movies_cache") or await _get_sorted_movies()
    context.user_data["movies_cache"] = movies
    text, kb = paginated_list(movies, int(page_str), "m", format_movie_list_item)
    await query.edit_message_text(text, reply_markup=kb)


@whitelist_only
async def movie_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, movie_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🎬 Movie detail #%s", update.effective_user.full_name, update.effective_user.id, movie_id_str)
    movie = await get_radarr().get_movie(int(movie_id_str))
    text = format_movie_detail(movie)
    await query.edit_message_text(text, reply_markup=movie_detail_keyboard(movie), parse_mode="HTML")


@whitelist_only
async def movie_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, movie_id_str = parse_callback(query.data)
    movie = await get_radarr().get_movie(int(movie_id_str))
    movie["monitored"] = not movie["monitored"]
    movie = await get_radarr().update_movie(movie)
    state = "📡 monitored" if movie["monitored"] else "📴 unmonitored"
    logger.info("User %s (%s) → 🎬 Movie '%s' → %s", update.effective_user.full_name, update.effective_user.id, movie["title"], state)
    await query.answer(f"Movie {state}.")
    context.user_data.pop("movies_cache", None)
    text = format_movie_detail(movie)
    await query.edit_message_text(text, reply_markup=movie_detail_keyboard(movie), parse_mode="HTML")


@whitelist_only
async def movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, movie_id_str = parse_callback(query.data)
    logger.info("User %s (%s) → 🔍 Search movie #%s", update.effective_user.full_name, update.effective_user.id, movie_id_str)
    await get_radarr().search_movie(int(movie_id_str))
    await query.answer("🔍 Search triggered!", show_alert=True)


@whitelist_only
async def movie_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, movie_id_str = parse_callback(query.data)
    movie_id = int(movie_id_str)
    logger.info("User %s (%s) → 🗑 Delete movie #%s (confirming)", update.effective_user.full_name, update.effective_user.id, movie_id_str)
    await query.edit_message_text(
        "⚠️ Are you sure you want to delete this movie?",
        reply_markup=delete_confirm_keyboard("m", movie_id),
    )


@whitelist_only
async def movie_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, _, movie_id_str, delete_files_str = parse_callback(query.data)
    delete_files = delete_files_str == "1"
    logger.info("User %s (%s) → 🗑 Confirmed delete movie #%s (files=%s)", update.effective_user.full_name, update.effective_user.id, movie_id_str, delete_files)
    await get_radarr().delete_movie(int(movie_id_str), delete_files=delete_files)
    context.user_data.pop("movies_cache", None)
    action = "🗑 Deleted with files removed" if delete_files else "🗑 Deleted (files kept)"
    await query.answer(f"{action}.", show_alert=True)
    await query.edit_message_text(f"{action}.")


@whitelist_only
async def movie_back_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    logger.info("User %s (%s) → ⬅️ Back to movies list", update.effective_user.full_name, update.effective_user.id)
    movies = await _get_sorted_movies()
    context.user_data["movies_cache"] = movies
    if not movies:
        await query.edit_message_text("🎬 No movies in library.")
        return
    text, kb = paginated_list(movies, 0, "m", format_movie_list_item)
    await query.edit_message_text(text, reply_markup=kb)
