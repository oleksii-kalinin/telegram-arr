from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Coroutine

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings

logger = logging.getLogger(__name__)


def whitelist_only(
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> Callable[..., Coroutine[Any, Any, Any]]:
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        user = update.effective_user
        if not user or user.id not in settings.allowed_users:
            uid = user.id if user else "unknown"
            name = user.full_name if user else "unknown"
            logger.warning("🚫 Access denied for %s (%s)", name, uid)
            if update.callback_query:
                await update.callback_query.answer("🚫 Access denied.", show_alert=True)
            elif update.message:
                await update.message.reply_text("🚫 Access denied.")
            return
        return await func(update, context)

    return wrapper
