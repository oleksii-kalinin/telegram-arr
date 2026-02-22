import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update):
        text = "An unexpected error occurred."
        if update.callback_query:
            await update.callback_query.answer(text[:200], show_alert=True)
        elif update.message:
            await update.message.reply_text(text[:4000])
