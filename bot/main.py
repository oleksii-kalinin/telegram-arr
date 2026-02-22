import logging
import re

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import settings
from bot.keyboards import (
    BTN_SEARCH, BTN_MOVIES, BTN_SHOWS, BTN_ACTIVITY, BTN_HELP,
    BTN_SEARCH_MOVIES, BTN_SEARCH_SHOWS, BTN_CANCEL,
)
from bot.handlers.start import start_cmd, help_cmd
from bot.handlers.search import (
    search_cmd,
    search_type_chosen,
    search_cancel,
    search_query_received,
    CHOOSE_TYPE,
    TYPE_QUERY,
)
from bot.handlers.movies import (
    movies_cmd,
    movie_page,
    movie_detail,
    movie_monitor,
    movie_search,
    movie_delete,
    movie_confirm_delete,
    movie_back_list,
)
from bot.handlers.shows import (
    shows_cmd,
    show_page,
    show_detail,
    show_monitor,
    show_search,
    show_delete,
    show_confirm_delete,
    show_seasons,
    show_season_detail,
    show_season_monitor,
    show_season_search,
    show_back_list,
    show_back_detail,
)
from bot.handlers.activity import activity_cmd, activity_refresh
from bot.handlers.errors import error_handler
from bot.clients.radarr import close_radarr
from bot.clients.sonarr import close_sonarr

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _exact(text: str) -> str:
    """Create an exact-match regex pattern, escaping special chars."""
    return f"^{re.escape(text)}$"


def main() -> None:
    app = ApplicationBuilder().token(settings.bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("movies", movies_cmd))
    app.add_handler(CommandHandler("shows", shows_cmd))
    app.add_handler(CommandHandler("activity", activity_cmd))

    # Reply keyboard button handlers
    app.add_handler(MessageHandler(filters.Regex(_exact(BTN_MOVIES)), movies_cmd))
    app.add_handler(MessageHandler(filters.Regex(_exact(BTN_SHOWS)), shows_cmd))
    app.add_handler(MessageHandler(filters.Regex(_exact(BTN_ACTIVITY)), activity_cmd))
    app.add_handler(MessageHandler(filters.Regex(_exact(BTN_HELP)), help_cmd))

    # Search conversation
    cancel_filter = filters.Regex(_exact(BTN_CANCEL))
    search_filter = filters.Regex(_exact(BTN_SEARCH))
    type_filter = filters.Regex(f"^({re.escape(BTN_SEARCH_MOVIES)}|{re.escape(BTN_SEARCH_SHOWS)})$")

    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_cmd),
            MessageHandler(search_filter, search_cmd),
        ],
        states={
            CHOOSE_TYPE: [
                MessageHandler(type_filter, search_type_chosen),
                MessageHandler(cancel_filter, search_cancel),
            ],
            TYPE_QUERY: [
                MessageHandler(cancel_filter, search_cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_query_received),
            ],
        },
        fallbacks=[
            CommandHandler("search", search_cmd),
            MessageHandler(search_filter, search_cmd),
            MessageHandler(cancel_filter, search_cancel),
        ],
        per_message=False,
    )
    app.add_handler(search_conv)

    # Add from search results
    from bot.handlers.search import add_from_search, quality_chosen, confirm_add, toggle_season, final_add_show

    app.add_handler(CallbackQueryHandler(add_from_search, pattern=r"^add:[ms]:\d+$"))
    app.add_handler(CallbackQueryHandler(quality_chosen, pattern=r"^qadd:[ms]:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(confirm_add, pattern=r"^radd:[ms]:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(toggle_season, pattern=r"^stog:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(final_add_show, pattern=r"^cfadd:\d+$"))

    # Movie callbacks
    app.add_handler(CallbackQueryHandler(movie_page, pattern=r"^page:m:\d+$"))
    app.add_handler(CallbackQueryHandler(movie_detail, pattern=r"^det:m:\d+$"))
    app.add_handler(CallbackQueryHandler(movie_monitor, pattern=r"^mon:m:\d+$"))
    app.add_handler(CallbackQueryHandler(movie_search, pattern=r"^tsr:m:\d+$"))
    app.add_handler(CallbackQueryHandler(movie_delete, pattern=r"^del:m:\d+$"))
    app.add_handler(
        CallbackQueryHandler(movie_confirm_delete, pattern=r"^cfd:m:\d+:\d$")
    )
    app.add_handler(CallbackQueryHandler(movie_back_list, pattern=r"^back:mlist$"))

    # Show callbacks
    app.add_handler(CallbackQueryHandler(show_page, pattern=r"^page:s:\d+$"))
    app.add_handler(CallbackQueryHandler(show_detail, pattern=r"^det:s:\d+$"))
    app.add_handler(CallbackQueryHandler(show_monitor, pattern=r"^mon:s:\d+$"))
    app.add_handler(CallbackQueryHandler(show_search, pattern=r"^tsr:s:\d+$"))
    app.add_handler(CallbackQueryHandler(show_delete, pattern=r"^del:s:\d+$"))
    app.add_handler(
        CallbackQueryHandler(show_confirm_delete, pattern=r"^cfd:s:\d+:\d$")
    )
    app.add_handler(CallbackQueryHandler(show_seasons, pattern=r"^sea:\d+$"))
    app.add_handler(CallbackQueryHandler(show_season_detail, pattern=r"^sead:\d+:\d+$"))
    app.add_handler(
        CallbackQueryHandler(show_season_monitor, pattern=r"^smon:\d+:\d+$")
    )
    app.add_handler(CallbackQueryHandler(show_season_search, pattern=r"^tssr:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(show_back_list, pattern=r"^back:slist$"))
    app.add_handler(CallbackQueryHandler(show_back_detail, pattern=r"^back:s:\d+$"))

    # Activity callbacks
    app.add_handler(CallbackQueryHandler(activity_refresh, pattern=r"^act:refresh$"))

    # Error handler
    app.add_error_handler(error_handler)

    # Cleanup on shutdown
    async def _shutdown(_app):
        await close_radarr()
        await close_sonarr()

    app.post_shutdown(_shutdown)

    logger.info("🚀 Bot starting...")
    app.run_polling()
