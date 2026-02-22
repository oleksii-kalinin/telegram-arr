from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_users: list[int] = field(default_factory=list)

    radarr_url: str = ""
    radarr_key: str = ""

    sonarr_url: str = ""
    sonarr_key: str = ""

    page_size: int = 5

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        allowed_raw = os.getenv("ALLOWED_USERS", "")
        allowed_users = [int(u.strip()) for u in allowed_raw.split(",") if u.strip()]
        return cls(
            bot_token=os.environ["BOT_TOKEN"],
            allowed_users=allowed_users,
            radarr_url=os.getenv("RADARR_URL", ""),
            radarr_key=os.getenv("RADARR_KEY", ""),
            sonarr_url=os.getenv("SONARR_URL", ""),
            sonarr_key=os.getenv("SONARR_KEY", ""),
            page_size=int(os.getenv("PAGE_SIZE", "5")),
        )


def _validate(s: Settings) -> None:
    errors = []
    if not s.bot_token:
        errors.append("BOT_TOKEN is required")
    if not s.allowed_users:
        errors.append("ALLOWED_USERS must contain at least one user ID")
    has_radarr = s.radarr_url and s.radarr_key
    has_sonarr = s.sonarr_url and s.sonarr_key
    if not has_radarr and not has_sonarr:
        errors.append("At least one of Radarr (RADARR_URL + RADARR_KEY) or Sonarr (SONARR_URL + SONARR_KEY) must be configured")
    if errors:
        raise SystemExit("Configuration error:\n  - " + "\n  - ".join(errors))


settings = Settings.from_env()
_validate(settings)
