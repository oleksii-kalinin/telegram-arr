import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import main_menu_keyboard
from bot.middleware import whitelist_only

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 <b>Available commands:</b>\n\n"
    "🔍 /search — Search for movies or TV shows to add\n"
    "🎬 /movies — Browse your movie library\n"
    "📺 /shows — Browse your TV show library\n"
    "📥 /activity — View download queue\n"
    "❓ /help — Show this message"
)


@whitelist_only
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info("User %s (%s) → /start", user.full_name, user.id)
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n{HELP_TEXT}",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@whitelist_only
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info("User %s (%s) → /help", user.full_name, user.id)
    await update.message.reply_text(HELP_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")
