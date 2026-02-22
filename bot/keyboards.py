from __future__ import annotations

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.config import settings

# Button labels (used for matching in handlers too)
BTN_SEARCH = "🔍 Search"
BTN_MOVIES = "🎬 Movies"
BTN_SHOWS = "📺 TV Shows"
BTN_ACTIVITY = "📥 Activity"
BTN_HELP = "❓ Help"

# Search sub-menu labels
BTN_SEARCH_MOVIES = "🎬 Search Movies"
BTN_SEARCH_SHOWS = "📺 Search TV Shows"
BTN_CANCEL = "❌ Cancel"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_SEARCH], [BTN_MOVIES, BTN_SHOWS], [BTN_ACTIVITY], [BTN_HELP]],
        resize_keyboard=True,
    )


def search_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_SEARCH_MOVIES, BTN_SEARCH_SHOWS], [BTN_CANCEL]],
        resize_keyboard=True,
    )


def search_input_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_CANCEL]],
        resize_keyboard=True,
    )


def paginated_list(
    items: list[dict[str, Any]],
    page: int,
    media_type: str,
    format_func: Any,
) -> tuple[str, InlineKeyboardMarkup]:
    ps = settings.page_size
    total_pages = max(1, (len(items) + ps - 1) // ps)
    page = max(0, min(page, total_pages - 1))
    page_items = items[page * ps : (page + 1) * ps]

    icon = "🎬" if media_type == "m" else "📺"
    lines = [f"{icon} Page {page + 1}/{total_pages}\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for item in page_items:
        lines.append(format_func(item))
        buttons.append(
            [
                InlineKeyboardButton(
                    item["title"],
                    callback_data=f"det:{media_type}:{item['id']}",
                )
            ]
        )

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{media_type}:{page - 1}")
        )
    if page < total_pages - 1:
        nav.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"page:{media_type}:{page + 1}")
        )
    if nav:
        buttons.append(nav)

    return "\n".join(lines), InlineKeyboardMarkup(buttons)


def movie_detail_keyboard(movie: dict[str, Any]) -> InlineKeyboardMarkup:
    movie_id = movie["id"]
    mon_label = "📴 Unmonitor" if movie.get("monitored") else "📡 Monitor"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(mon_label, callback_data=f"mon:m:{movie_id}"),
                InlineKeyboardButton("🔍 Search", callback_data=f"tsr:m:{movie_id}"),
            ],
            [
                InlineKeyboardButton("🗑 Delete", callback_data=f"del:m:{movie_id}"),
                InlineKeyboardButton("⬅️ Back", callback_data="back:mlist"),
            ],
        ]
    )


def show_detail_keyboard(show: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = show["id"]
    mon_label = "📴 Unmonitor" if show.get("monitored") else "📡 Monitor"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(mon_label, callback_data=f"mon:s:{sid}"),
                InlineKeyboardButton("🔍 Search", callback_data=f"tsr:s:{sid}"),
            ],
            [
                InlineKeyboardButton("📂 Seasons", callback_data=f"sea:{sid}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"del:s:{sid}"),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back:slist")],
        ]
    )


def season_list_keyboard(show: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = show["id"]
    buttons: list[list[InlineKeyboardButton]] = []
    for season in sorted(show.get("seasons", []), key=lambda s: s["seasonNumber"]):
        sn = season["seasonNumber"]
        label = "⭐ Specials" if sn == 0 else f"📂 Season {sn}"
        buttons.append(
            [InlineKeyboardButton(label, callback_data=f"sead:{sid}:{sn}")]
        )
    buttons.append(
        [InlineKeyboardButton("⬅️ Back", callback_data=f"back:s:{sid}")]
    )
    return InlineKeyboardMarkup(buttons)


def season_detail_keyboard(
    series_id: int, season_number: int, monitored: bool
) -> InlineKeyboardMarkup:
    mon_label = "📴 Unmonitor" if monitored else "📡 Monitor"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    mon_label, callback_data=f"smon:{series_id}:{season_number}"
                ),
                InlineKeyboardButton(
                    "🔍 Search Season",
                    callback_data=f"tssr:{series_id}:{season_number}",
                ),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"sea:{series_id}")],
        ]
    )


def delete_confirm_keyboard(
    media_type: str, item_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📁 Keep files",
                    callback_data=f"cfd:{media_type}:{item_id}:0",
                ),
                InlineKeyboardButton(
                    "🗑 Remove files",
                    callback_data=f"cfd:{media_type}:{item_id}:1",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"det:{media_type}:{item_id}",
                )
            ],
        ]
    )


def quality_profile_keyboard(
    profiles: list[dict[str, Any]], media_type: str, item_id: int
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for p in profiles:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎯 {p['name']}",
                    callback_data=f"qadd:{media_type}:{item_id}:{p['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons)


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024**4:
        return f"{size_bytes / 1024**4:.1f} TB"
    if size_bytes >= 1024**3:
        return f"{size_bytes / 1024**3:.1f} GB"
    return f"{size_bytes / 1024**2:.0f} MB"


def root_folder_keyboard(
    folders: list[dict[str, Any]], media_type: str, item_id: int
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for f in folders:
        path = f.get("path", "?")
        free = f.get("freeSpace", 0)
        label = f"📁 {path} ({_format_size(free)} free)"
        buttons.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"radd:{media_type}:{item_id}:{f['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons)


def search_results_keyboard(
    results: list[dict[str, Any]], media_type: str, existing_ids: set[int]
) -> InlineKeyboardMarkup:
    id_key = "tmdbId" if media_type == "m" else "tvdbId"
    buttons: list[list[InlineKeyboardButton]] = []
    for item in results[:10]:
        item_id = item.get(id_key, 0)
        title = item.get("title", "Unknown")[:30]
        year = item.get("year", "?")
        if item_id in existing_ids:
            buttons.append(
                [InlineKeyboardButton(f"✅ {title} ({year})", callback_data=f"noop:{item_id}")]
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"➕ {title} ({year})",
                        callback_data=f"add:{media_type}:{item_id}",
                    )
                ]
            )
    return InlineKeyboardMarkup(buttons)


def season_select_keyboard(
    tvdb_id: int, seasons: list[dict[str, Any]]
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for s in sorted(seasons, key=lambda x: x["seasonNumber"]):
        sn = s["seasonNumber"]
        mon = s.get("monitored", True)
        icon = "✅" if mon else "⬜"
        label = "Specials" if sn == 0 else f"Season {sn}"
        buttons.append(
            [InlineKeyboardButton(f"{icon} {label}", callback_data=f"stog:{tvdb_id}:{sn}")]
        )
    buttons.append(
        [InlineKeyboardButton("📡 Confirm & Add", callback_data=f"cfadd:{tvdb_id}")]
    )
    return InlineKeyboardMarkup(buttons)


def activity_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔄 Refresh", callback_data="act:refresh")]]
    )
