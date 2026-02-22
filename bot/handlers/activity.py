from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.clients.radarr import get_radarr
from bot.clients.sonarr import get_sonarr
from bot.formatting import format_queue
from bot.keyboards import activity_keyboard, main_menu_keyboard
from bot.middleware import whitelist_only

logger = logging.getLogger(__name__)


async def _fetch_queue() -> tuple[list, list]:
    radarr = get_radarr()
    sonarr = get_sonarr()
    radarr_data = await radarr.get_queue(page=1, page_size=50)
    sonarr_data = await sonarr.get_queue(page=1, page_size=50)
    return radarr_data.get("records", []), sonarr_data.get("records", [])


@whitelist_only
async def activity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info("User %s (%s) → activity", user.full_name, user.id)
    radarr_records, sonarr_records = await _fetch_queue()
    text = format_queue(radarr_records, sonarr_records)
    await update.message.reply_text(
        text,
        reply_markup=activity_keyboard(),
        parse_mode="HTML",
    )


@whitelist_only
async def activity_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    logger.info("User %s (%s) → refresh activity", user.full_name, user.id)
    radarr_records, sonarr_records = await _fetch_queue()
    text = format_queue(radarr_records, sonarr_records)
    await query.edit_message_text(
        text,
        reply_markup=activity_keyboard(),
        parse_mode="HTML",
    )
