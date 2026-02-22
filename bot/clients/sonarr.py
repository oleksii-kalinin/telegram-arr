from __future__ import annotations

from typing import Any

from bot.clients.base import BaseArrClient
from bot.config import settings


class SonarrClient(BaseArrClient):
    def __init__(self) -> None:
        super().__init__(settings.sonarr_url, settings.sonarr_key)

    async def get_series(self) -> list[dict[str, Any]]:
        return await self._get("/series")

    async def get_show(self, series_id: int) -> dict[str, Any]:
        return await self._get(f"/series/{series_id}")

    async def lookup(self, term: str) -> list[dict[str, Any]]:
        return await self._get("/series/lookup", term=term)

    async def get_quality_profiles(self) -> list[dict[str, Any]]:
        return await self._get("/qualityprofile")

    async def get_root_folders(self) -> list[dict[str, Any]]:
        return await self._get("/rootfolder")

    async def get_queue(self, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return await self._get("/queue", page=page, pageSize=page_size, includeUnknownSeriesItems="false")

    async def add_series(self, show: dict[str, Any], quality_profile_id: int, root_folder_path: str) -> dict[str, Any]:
        payload = dict(show)
        payload["qualityProfileId"] = quality_profile_id
        payload["rootFolderPath"] = root_folder_path
        payload["monitored"] = True
        payload["addOptions"] = {"searchForMissingEpisodes": True}
        payload.pop("id", None)
        return await self._post("/series", json=payload)

    async def update_series(self, show: dict[str, Any]) -> dict[str, Any]:
        return await self._put(f"/series/{show['id']}", json=show)

    async def delete_series(
        self, series_id: int, delete_files: bool = False
    ) -> None:
        await self._delete(
            f"/series/{series_id}",
            deleteFiles=str(delete_files).lower(),
        )

    async def get_episodes(self, series_id: int) -> list[dict[str, Any]]:
        return await self._get("/episode", seriesId=series_id)

    async def search_series(self, series_id: int) -> dict[str, Any]:
        return await self._post(
            "/command",
            json={"name": "SeriesSearch", "seriesId": series_id},
        )

    async def search_season(
        self, series_id: int, season_number: int
    ) -> dict[str, Any]:
        return await self._post(
            "/command",
            json={
                "name": "SeasonSearch",
                "seriesId": series_id,
                "seasonNumber": season_number,
            },
        )


_instance: SonarrClient | None = None


def get_sonarr() -> SonarrClient:
    global _instance
    if _instance is None:
        _instance = SonarrClient()
    return _instance


async def close_sonarr() -> None:
    global _instance
    if _instance is not None:
        await _instance.close()
        _instance = None
