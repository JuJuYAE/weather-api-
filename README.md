# Weather Playability Summary (Telegram)

Hourly weather → playable windows → a clean Telegram summary.

This project fetches hourly weather from Open‑Meteo, filters for your preferred play times, scores the best windows, and sends a Telegram message you can read at a glance.

## Features

- Pulls hourly forecast data for your exact location
- Filters by weekday/weekend time windows
- Scores each session for “tennis vibes”
- Ranks and formats the top windows for Telegram

## How It Works

1. Fetch hourly data from Open‑Meteo
2. Build a DataFrame
3. Filter to playable hours (`helpers/playability.py`)
4. Merge consecutive hours into windows + score them (`helpers/summary.py`)
5. Send the summary to Telegram

## Project Layout

- `send_summary.py` — main script (fetch → filter → format → send)
- `helpers/playability.py` — playable rules + scoring
- `helpers/summary.py` — window building + message formatting
- `requirements.in` — top‑level deps (unlocked)
- `requirements.txt` — pinned deps (generated)
- `Dockerfile` — Railway-ready container

## Environment Variables

Create a `.env` file (or set these in Railway):

- `TELEGRAM_TOKEN` — your bot token
- `CHAT_ID` — target chat id
- `NEWHAM_LAT` — latitude
- `NEWHAM_LON` — longitude

Example:

```env
TELEGRAM_TOKEN=123456:ABCDEF...
CHAT_ID=123456789
NEWHAM_LAT=51.5074
NEWHAM_LON=0.1278
```

## Run Locally

```bash
pip install -r requirements.txt
python send_summary.py
```

## Docker

```bash
docker build -t weather-summary .
docker run --env-file .env weather-summary
```

## Customize

- Change playable rules in `helpers/playability.py`.
- Adjust scoring or formatting in `helpers/summary.py`.

## Railway Notes

- Deploy with the Dockerfile
- Set the environment variables in Railway’s dashboard
- Schedule with Railway cron if desired
