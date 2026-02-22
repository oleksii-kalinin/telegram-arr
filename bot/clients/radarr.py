from __future__ import annotations

from typing import Any

from bot.clients.base import BaseArrClient
from bot.config import settings


class RadarrClient(BaseArrClient):
    def __init__(self) -> None:
        super().__init__(settings.radarr_url, settings.radarr_key)

    async def get_movies(self) -> list[dict[str, Any]]:
        return await self._get("/movie")

    async def get_movie(self, movie_id: int) -> dict[str, Any]:
        return await self._get(f"/movie/{movie_id}")

    async def lookup(self, term: str) -> list[dict[str, Any]]:
        return await self._get("/movie/lookup", term=term)

    async def get_quality_profiles(self) -> list[dict[str, Any]]:
        return await self._get("/qualityprofile")

    async def get_root_folders(self) -> list[dict[str, Any]]:
        return await self._get("/rootfolder")

    async def get_queue(self, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return await self._get("/queue", page=page, pageSize=page_size, includeUnknownMovieItems="false")

    async def add_movie(self, movie: dict[str, Any], quality_profile_id: int, root_folder_path: str) -> dict[str, Any]:
        payload = dict(movie)
        payload["qualityProfileId"] = quality_profile_id
        payload["rootFolderPath"] = root_folder_path
        payload["monitored"] = True
        payload["addOptions"] = {"searchForMovie": True}
        payload.pop("id", None)
        return await self._post("/movie", json=payload)

    async def update_movie(self, movie: dict[str, Any]) -> dict[str, Any]:
        return await self._put(f"/movie/{movie['id']}", json=movie)

    async def delete_movie(
        self, movie_id: int, delete_files: bool = False
    ) -> None:
        await self._delete(
            f"/movie/{movie_id}",
            deleteFiles=str(delete_files).lower(),
            addImportExclusion="false",
        )

    async def search_movie(self, movie_id: int) -> dict[str, Any]:
        return await self._post(
            "/command",
            json={"name": "MoviesSearch", "movieIds": [movie_id]},
        )


_instance: RadarrClient | None = None


def get_radarr() -> RadarrClient:
    global _instance
    if _instance is None:
        _instance = RadarrClient()
    return _instance


async def close_radarr() -> None:
    global _instance
    if _instance is not None:
        await _instance.close()
        _instance = None
