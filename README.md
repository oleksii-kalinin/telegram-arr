# Telegram Sonarr/Radarr Bot

A Telegram bot for managing your Sonarr and Radarr libraries via inline keyboards.

## Features

- Browse and search your movie/TV show libraries with paginated lists
- Add new movies and shows from search results
- Monitor/unmonitor movies, shows, and individual seasons
- Trigger downloads directly from Telegram
- Delete movies/shows with file management options
- Whitelist-based access control

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | List available commands |
| `/search` | Search for movies or TV shows to add |
| `/movies` | Browse your movie library |
| `/shows` | Browse your TV show library |

## Setup

### 1. Create a Telegram bot

Message [@BotFather](https://t.me/BotFather) on Telegram and use `/newbot` to get a bot token.

### 2. Get your Telegram user ID

Message [@userinfobot](https://t.me/userinfobot) to get your numeric user ID.

### 3. Get your API keys

- **Radarr**: Settings > General > API Key
- **Sonarr**: Settings > General > API Key

Quality profile IDs can be found via `GET /api/v3/qualityprofile` on your Radarr/Sonarr instance.

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
BOT_TOKEN=your_bot_token
ALLOWED_USERS=123456789,987654321

RADARR_URL=http://192.168.1.10:7878/api/v3
RADARR_KEY=your_key
RADARR_QUALITY_PROFILE_ID=1
RADARR_ROOT_FOLDER_PATH=/movies

SONARR_URL=http://192.168.1.10:8989/api/v3
SONARR_KEY=your_key
SONARR_QUALITY_PROFILE_ID=1
SONARR_ROOT_FOLDER_PATH=/tv

PAGE_SIZE=5
```

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `ALLOWED_USERS` | Comma-separated Telegram user IDs that can use the bot |
| `RADARR_URL` | Radarr API base URL (include `/api/v3`) |
| `RADARR_KEY` | Radarr API key |
| `RADARR_QUALITY_PROFILE_ID` | Quality profile ID for new movies |
| `RADARR_ROOT_FOLDER_PATH` | Root folder path for new movies |
| `SONARR_URL` | Sonarr API base URL (include `/api/v3`) |
| `SONARR_KEY` | Sonarr API key |
| `SONARR_QUALITY_PROFILE_ID` | Quality profile ID for new shows |
| `SONARR_ROOT_FOLDER_PATH` | Root folder path for new shows |
| `PAGE_SIZE` | Items per page when browsing (default: 5) |

## Running

### Docker (recommended)

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

### Manual

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bot
```
