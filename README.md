# PostToVideo Bot

Telegram bot that turns Uzbek text messages into short captioned videos.

## Run locally

1. Install Python 3.11 and FFmpeg.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Set `BOT_TOKEN` and `ADMIN_IDS` in your environment (or a local `.env` file).
   `ADMIN_IDS` is a comma-separated list of Telegram numeric user IDs allowed to
   use `/setlogo`.
4. Start the bot with `python -m bot`.

Run tests with `python -m unittest discover -v`.

Default background and logo files are in `logos/`. Runtime database, custom
logos, and temporary video files are stored under the project directory unless
paths are overridden with `DB_PATH`, `LOGOS_DIR`, and `TMP_DIR`.

## Docker

Build and run:

```powershell
docker build -t posttovideo .
docker run --rm -e BOT_TOKEN=your-token -e ADMIN_IDS=123456789 posttovideo
```

`.dockerignore` keeps local Claude settings, credentials, databases, and caches
out of the image.

## Render free Web Service

Locally the bot uses Telegram long polling. When `WEBHOOK_BASE_URL` is set, it
switches to webhook mode and serves HTTP on `0.0.0.0:$PORT`, which is suitable
for Render's free Web Service.

1. Push the project to a GitHub repository and create a **Web Service** on
   Render connected to that repository. Select the Docker runtime and the
   **Free** instance type.
2. Set these environment variables in Render:
   - `BOT_TOKEN`: the Telegram bot token.
   - `ADMIN_IDS`: comma-separated Telegram numeric user IDs allowed to use
     `/setlogo`.
   - `WEBHOOK_BASE_URL`: the service's public URL, for example
     `https://your-service.onrender.com` (no trailing slash).
   - `WEBHOOK_SECRET_TOKEN`: a private random value using only letters,
     numbers, underscores, and hyphens.
3. Keep `PORT` unset; Render supplies it. `WEBHOOK_PATH` defaults to
   `/telegram`. Render's health check can use `/healthz`.

Render's free Web Services spin down after inactivity and have ephemeral
storage. The bot may take about a minute to wake when Telegram sends an update,
and the local SQLite database and uploaded logos are not durable. Free Render
services cannot attach persistent disks; use paid storage or an external
database/object store if that data must persist. Free instances are intended
for testing and hobby projects, not production.
