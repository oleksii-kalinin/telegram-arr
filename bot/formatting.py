from __future__ import annotations

from html import escape
from typing import Any


def _status_icon(item: dict[str, Any]) -> str:
    if not item.get("monitored"):
        return "⏸️"
    if item.get("hasFile") or item.get("statistics", {}).get("percentOfEpisodes", 0) == 100:
        return "✅"
    return "❌"


def format_movie_list_item(movie: dict[str, Any]) -> str:
    icon = _status_icon(movie)
    return f"{icon} {escape(movie['title'])} ({movie.get('year', '?')})"


def format_movie_detail(movie: dict[str, Any]) -> str:
    status = "📡 Monitored" if movie.get("monitored") else "📴 Unmonitored"
    has_file = "✅ Yes" if movie.get("hasFile") else "❌ No"
    size = movie.get("sizeOnDisk", 0)
    size_str = f"💾 {size / (1024**3):.1f} GB" if size else "💾 N/A"

    lines = [
        f"🎬 <b>{escape(movie['title'])}</b> ({movie.get('year', '?')})",
        "",
        f"Status: {status}",
        f"Downloaded: {has_file}",
        f"Size: {size_str}",
    ]
    overview = movie.get("overview", "")
    if overview:
        lines.append(f"\n📝 <i>{escape(overview[:300])}</i>")
    return "\n".join(lines)


def format_show_list_item(show: dict[str, Any]) -> str:
    icon = _status_icon(show)
    return f"{icon} {escape(show['title'])} ({show.get('year', '?')})"


def format_show_detail(show: dict[str, Any]) -> str:
    status = "📡 Monitored" if show.get("monitored") else "📴 Unmonitored"
    stats = show.get("statistics", {})
    ep_count = stats.get("episodeFileCount", 0)
    ep_total = stats.get("totalEpisodeCount", 0)
    size = stats.get("sizeOnDisk", 0)
    size_str = f"💾 {size / (1024**3):.1f} GB" if size else "💾 N/A"
    seasons = stats.get("seasonCount", 0)

    lines = [
        f"📺 <b>{escape(show['title'])}</b> ({show.get('year', '?')})",
        "",
        f"Status: {status}",
        f"📂 Seasons: {seasons}",
        f"🎞️ Episodes: {ep_count}/{ep_total}",
        f"Size: {size_str}",
    ]
    overview = show.get("overview", "")
    if overview:
        lines.append(f"\n📝 <i>{escape(overview[:300])}</i>")
    return "\n".join(lines)


def format_season_list(show: dict[str, Any], episodes: list[dict[str, Any]]) -> str:
    lines = [f"📺 <b>{escape(show['title'])}</b> — Seasons"]
    for season in sorted(show.get("seasons", []), key=lambda s: s["seasonNumber"]):
        sn = season["seasonNumber"]
        if sn == 0:
            label = "⭐ Specials"
        else:
            label = f"📂 Season {sn}"
        season_eps = [e for e in episodes if e.get("seasonNumber") == sn]
        downloaded = sum(1 for e in season_eps if e.get("hasFile"))
        total = len(season_eps)
        mon = "📡" if season.get("monitored") else "📴"
        lines.append(f"  {label}: {downloaded}/{total} {mon}")
    return "\n".join(lines)


def format_season_detail(
    show: dict[str, Any], season_number: int, episodes: list[dict[str, Any]]
) -> str:
    season_eps = [e for e in episodes if e.get("seasonNumber") == season_number]
    season_eps.sort(key=lambda e: e.get("episodeNumber", 0))

    season = next(
        (s for s in show.get("seasons", []) if s["seasonNumber"] == season_number),
        {},
    )
    mon = "📡 Monitored" if season.get("monitored") else "📴 Unmonitored"

    label = "⭐ Specials" if season_number == 0 else f"📂 Season {season_number}"
    downloaded = sum(1 for e in season_eps if e.get("hasFile"))

    lines = [
        f"📺 <b>{escape(show['title'])}</b> — {label}",
        "",
        f"Status: {mon}",
        f"🎞️ Episodes: {downloaded}/{len(season_eps)}",
    ]
    return "\n".join(lines)


def _progress_bar(percent: float, width: int = 10) -> str:
    filled = round(percent / 100 * width)
    return "▓" * filled + "░" * (width - filled)


def _eta_str(time_left: str | None) -> str:
    if not time_left:
        return "⏳ --:--"
    # Sonarr/Radarr return HH:MM:SS or similar
    parts = time_left.split(":")
    if len(parts) >= 2:
        h, m = int(parts[0]), int(parts[1])
        if h > 0:
            return f"⏳ {h}h {m}m"
        return f"⏳ {m}m"
    return f"⏳ {time_left}"


def format_queue(radarr_records: list[dict[str, Any]], sonarr_records: list[dict[str, Any]]) -> str:
    if not radarr_records and not sonarr_records:
        return "📥 <b>Activity</b>\n\n😴 Nothing in the queue!"

    lines = ["📥 <b>Activity</b>\n"]

    if radarr_records:
        lines.append("🎬 <b>Movies</b>")
        for rec in radarr_records:
            lines.append(_format_queue_record(rec))
        lines.append("")

    if sonarr_records:
        lines.append("📺 <b>TV Shows</b>")
        for rec in sonarr_records:
            lines.append(_format_queue_record(rec))
        lines.append("")

    return "\n".join(lines)


def _format_queue_record(rec: dict[str, Any]) -> str:
    title = escape(rec.get("title", "Unknown"))
    status = rec.get("status", "unknown")
    size = rec.get("size", 0)
    remaining = rec.get("sizeleft", 0)
    time_left = rec.get("timeleft")

    if size > 0:
        percent = max(0, min(100, (1 - remaining / size) * 100))
    else:
        percent = 0

    bar = _progress_bar(percent)
    size_str = _format_dl_size(size)
    eta = _eta_str(time_left)

    status_icon = {
        "downloading": "⬇️",
        "paused": "⏸️",
        "queued": "🕐",
        "completed": "✅",
        "warning": "⚠️",
        "failed": "❌",
    }.get(status.lower(), "❓")

    return f"  {status_icon} <b>{title}</b>\n    {bar} {percent:.0f}% • {size_str} • {eta}"


def _format_dl_size(size_bytes: int) -> str:
    if size_bytes >= 1024**3:
        return f"{size_bytes / 1024**3:.1f} GB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / 1024**2:.0f} MB"
    return f"{size_bytes / 1024:.0f} KB"


def format_search_result(item: dict[str, Any], media_type: str) -> str:
    title = item.get("title", "Unknown")
    year = item.get("year", "?")
    overview = item.get("overview", "")[:200]
    icon = "🎬" if media_type == "m" else "📺"
    lines = [f"{icon} <b>{escape(title)}</b> ({year})"]
    if overview:
        lines.append(f"📝 <i>{escape(overview)}</i>")
    return "\n".join(lines)
