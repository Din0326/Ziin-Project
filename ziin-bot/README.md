# ziin bot (modernized)

## Requirements
- Python 3.12.3
- A Discord bot token

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (you can copy from `.env.example`) and set:
- `DISCORD_TOKEN`

### Local SQLite DB
Guild settings (Prefix/Language/TimeZone and other runtime data) are stored in a local SQLite file.

Optional:
1. Set `LOCAL_DB_PATH` in `.env` to customize the DB file path.

If not set, default path is `./data/local.db`.

## Run
```bash
python -m bot.main
```

## Project layout
- `bot/main.py` : entry point
- `bot/cogs/`   : all commands/events (legacy prefix commands preserved)
- `bot/services/storage.py` : shared SQLite-backed document store (Firestore-compatible API)
- `data/i18n/`  : translations

