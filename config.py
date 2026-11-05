"""Central configuration for the PostToVideo Bot.

Loads environment variables from a local ``.env`` file (via ``python-dotenv``)
and exposes the values the rest of the codebase depends on.
"""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

# Load variables from a .env file if one is present in the working directory.
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def _configured_path(name: str, default: str) -> str:
    """Return an environment-configured path, rooted at the project if relative."""
    path = os.getenv(name, default)
    if not os.path.isabs(path):
        path = os.path.join(PROJECT_DIR, path)
    return os.path.normpath(path)


def _parse_admin_ids(raw: str | None) -> List[int]:
    """Parse a comma/newline separated list of Telegram IDs into ``int``."""
    if not raw:
        return []
    ids: List[int] = []
    for chunk in raw.replace("\n", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(int(chunk))
        except ValueError:
            # Skip malformed entries instead of crashing on startup.
            continue
    return ids


# Telegram Bot API token. Required — the bot will refuse to start without it.
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/telegram")
WEBHOOK_SECRET_TOKEN: str = os.getenv("WEBHOOK_SECRET_TOKEN", "")
PORT: int = int(os.getenv("PORT", "10000"))

# Optional list of administrator user IDs (Telegram chat ids).
# Supports comma or newline separated values, e.g. ``123,456``.
ADMIN_IDS: List[int] = _parse_admin_ids(os.getenv("ADMIN_IDS"))

# Directory used for persisted media assets (logos, default background, etc.).
ASSETS_DIR: str = _configured_path("ASSETS_DIR", "logos")

# Directory used for uploaded custom logos.
LOGOS_DIR: str = _configured_path("LOGOS_DIR", "logos")

# Directory used for temporary render outputs before delivery.
TMP_DIR: str = _configured_path("TMP_DIR", "tmp")

# Default assets shipped with the project. They live inside ``ASSETS_DIR`` but
# can be overridden through environment variables if a deployment ships custom
# branding.
DEFAULT_BG_IMAGE: str = _configured_path(
    "DEFAULT_BG_IMAGE", os.path.join(ASSETS_DIR, "default_bg.jpg")
)
DEFAULT_LOGO_IMAGE: str = _configured_path(
    "DEFAULT_LOGO_IMAGE", os.path.join(ASSETS_DIR, "default_logo.png")
)

# Video rendering parameters (vertical mobile format).
VIDEO_WIDTH: int = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT: int = int(os.getenv("VIDEO_HEIGHT", "1920"))
VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "24"))

# Subtitle / branding layout constants.
SUBTITLE_MAX_WIDTH_RATIO: float = float(os.getenv("SUBTITLE_MAX_WIDTH_RATIO", "0.85"))
LOGO_MARGIN_PX: int = int(os.getenv("LOGO_MARGIN_PX", "40"))
LOGO_MAX_HEIGHT_RATIO: float = float(os.getenv("LOGO_MAX_HEIGHT_RATIO", "0.12"))

# Font configuration. ``fonts-liberation`` ships ``LiberationSans-Bold.ttf`` on
# Debian/Ubuntu — the exact path is probed at runtime so the bot works on
# either Linux or a local Windows dev box.
FONT_CANDIDATES: List[str] = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]

# gTTS language. Uzbek has limited direct coverage in the Google TTS engine,
# so we default to ``tr`` (Turkish) which produces a phonetically close and
# natural voice for Turkic-language text. Override with ``GTTS_LANG`` if you
# prefer ``en`` or another supported code.
GTTS_LANG: str = os.getenv("GTTS_LANG", "tr")

# Maximum number of text segments produced per post. Keeps every generated
# Short/Reel under a sane duration ceiling.
MAX_SEGMENTS: int = int(os.getenv("MAX_SEGMENTS", "18"))

# Per-segment minimum duration (seconds) so subtitles never flash too quickly.
MIN_SEGMENT_DURATION: float = float(os.getenv("MIN_SEGMENT_DURATION", "1.8"))