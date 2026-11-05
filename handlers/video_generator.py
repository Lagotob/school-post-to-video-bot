"""Telegram message handler and MoviePy-based video rendering pipeline."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import List, Optional

from aiogram import F, Router, types
from aiogram.types import FSInputFile
from gtts import gTTS
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    vfx,
)

from config import (
    ADMIN_IDS,
    DEFAULT_BG_IMAGE,
    DEFAULT_LOGO_IMAGE,
    FONT_CANDIDATES,
    GTTS_LANG,
    LOGO_MARGIN_PX,
    LOGO_MAX_HEIGHT_RATIO,
    MIN_SEGMENT_DURATION,
    SUBTITLE_MAX_WIDTH_RATIO,
    TMP_DIR,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from database import get_logo_path, upsert_user
from handlers.text_processor import split_text

router = Router()
logger = logging.getLogger(__name__)


async def generate_video(
    chat_id: int,
    text: str,
    output_path: str,
    max_words_per_segment: int = 4,
) -> None:
    """Render a video and keep synchronous media work off the bot event loop."""
    segments = split_text(text, max_words_per_segment)
    if not segments:
        raise ValueError("No valid text segments produced")

    background_path = DEFAULT_BG_IMAGE
    if not os.path.isfile(background_path):
        raise FileNotFoundError(f"Background media not found: {background_path}")

    logo_path = await get_logo_path(chat_id) or DEFAULT_LOGO_IMAGE
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo not found: {logo_path}")

    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    await asyncio.to_thread(_render_video, segments, background_path, logo_path, output_path)


def _render_video(
    segments: List[str],
    background_path: str,
    logo_path: str,
    output_path: str,
) -> None:
    """Create per-segment speech and subtitle clips with matching durations."""
    font_path = next((path for path in FONT_CANDIDATES if os.path.isfile(path)), None)
    if font_path is None:
        raise RuntimeError("No suitable font found")

    audio_clips: List[AudioFileClip] = []
    text_clips: List[TextClip] = []
    background_clip: Optional[ImageClip | VideoFileClip] = None
    final_clip: Optional[CompositeVideoClip] = None

    try:
        with tempfile.TemporaryDirectory(dir=TMP_DIR, prefix="posttovideo-") as work_dir:
            for index, segment in enumerate(segments):
                audio_path = os.path.join(work_dir, f"segment-{index}.mp3")
                gTTS(text=segment, lang=GTTS_LANG).save(audio_path)
                audio_clips.append(AudioFileClip(audio_path))

            segment_durations = [
                max(clip.duration, MIN_SEGMENT_DURATION) for clip in audio_clips
            ]
            total_duration = sum(segment_durations)
            audio_track = CompositeAudioClip(
                [
                    clip.with_start(sum(segment_durations[:index]))
                    for index, clip in enumerate(audio_clips)
                ]
            ).with_duration(total_duration)

            if background_path.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
                background_clip = VideoFileClip(background_path).with_effects(
                    [vfx.Loop(duration=total_duration)]
                )
            else:
                background_clip = ImageClip(background_path).with_duration(total_duration)
            background_clip = background_clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT))

            logo_height = max(1, int(VIDEO_HEIGHT * LOGO_MAX_HEIGHT_RATIO))
            logo_clip = ImageClip(logo_path).resized(height=logo_height)
            logo_clip = logo_clip.with_position(
                (VIDEO_WIDTH - logo_clip.w - LOGO_MARGIN_PX, LOGO_MARGIN_PX)
            ).with_duration(total_duration)

            start_time = 0.0
            for segment, duration in zip(segments, segment_durations):
                subtitle = TextClip(
                    font=font_path,
                    text=segment,
                    font_size=48,
                    color="white",
                    bg_color=(0, 0, 0),
                    size=(int(VIDEO_WIDTH * SUBTITLE_MAX_WIDTH_RATIO), None),
                    method="caption",
                ).with_duration(duration).with_start(start_time).with_position("center")
                text_clips.append(subtitle)
                start_time += duration

            final_clip = CompositeVideoClip(
                [background_clip, *text_clips, logo_clip],
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            ).with_duration(total_duration).with_audio(audio_track)
            final_clip.write_videofile(
                output_path,
                fps=VIDEO_FPS,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                preset="ultrafast",
                logger=None,
            )
    finally:
        if final_clip is not None:
            final_clip.close()
        for clip in text_clips:
            clip.close()
        if background_clip is not None:
            background_clip.close()
        for clip in audio_clips:
            clip.close()


@router.message(F.text)
async def handle_text_message(message: types.Message) -> None:
    """Turn a user's text message into a video and return it in Telegram."""
    if message.from_user is None or message.text is None:
        return
    if message.text.startswith("/"):
        return

    user = message.from_user
    await upsert_user(
        chat_id=message.chat.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.id in ADMIN_IDS,
    )

    status = await message.answer("Matn videoga aylantirilmoqda. Iltimos, kuting…")
    output_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp4", dir=TMP_DIR, prefix="video-", delete=False
        ) as output_file:
            output_path = output_file.name

        await generate_video(message.chat.id, message.text, output_path)
        await message.answer_video(
            FSInputFile(output_path),
            caption="Tayyor! 🎬",
        )
    except Exception:
        logger.exception("Video generation failed for chat %s", message.chat.id)
        await message.answer(
            "Videoni yaratishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko‘ring."
        )
    finally:
        await status.delete()
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
