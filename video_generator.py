"""Video rendering engine.

Handles the end-to-end media pipeline:
    1. Accept input text, look up the custom logo path in the database.
    2. Run ``gTTS`` to generate the audio layer.
    3. Construct the ``ImageClip`` or ``VideoFileClip`` background.
    4. Loop through the text segments to overlay individual text frames.
    5. Overlay the logo clip with a fixed margin from the top-right corner.
    6. Composite the project tracks using ``CompositeVideoClip`` and ``set_audio``.
    7. Compile and export to a compressed, mobile-friendly MP4 profile.
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional

from gtts import gTTS
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip

from config import (
    DEFAULT_BG_IMAGE,
    DEFAULT_LOGO_IMAGE,
    FONT_CANDIDATES,
    GTTS_LANG,
    LOGO_MARGIN_PX,
    LOGO_MAX_HEIGHT_RATIO,
    SUBTITLE_MAX_WIDTH_RATIO,
    TMP_DIR,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from database import get_logo_path
from handlers.text_processor import split_text


async def generate_video(
    chat_id: int,
    text: str,
    output_path: str,
    max_words_per_segment: int = 4,
) -> None:
    """Generate a video from text with synchronized subtitles and branding.

    Args:
        chat_id: Telegram chat id (used to look up custom logo).
        text: Raw announcement text in Uzbek (Latin script).
        output_path: Where to save the final MP4.
        max_words_per_segment: Maximum number of words per subtitle segment.

    Raises:
        RuntimeError: When the video generation fails.
    """
    # Make sure the output directory exists.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Split the text into subtitle-friendly segments.
    segments = split_text(text, max_words_per_segment)
    if not segments:
        raise RuntimeError("No valid text segments produced")

    # Generate the audio layer using gTTS.
    tts = gTTS(text=text, lang=GTTS_LANG)
    with tempfile.NamedTemporaryFile(suffix=".mp3", dir=TMP_DIR, delete=False) as tmp_audio:
        tts.save(tmp_audio.name)
        audio_clip = AudioFileClip(tmp_audio.name)

    # Determine the background media (image or video).
    bg_path = DEFAULT_BG_IMAGE
    if os.path.exists(bg_path):
        if bg_path.lower().endswith(".mp4"):
            bg_clip = VideoFileClip(bg_path)
        else:
            bg_clip = ImageClip(bg_path)
    else:
        raise RuntimeError(f"Background media not found: {bg_path}")

    # Resize the background to fit the target dimensions.
    bg_clip = bg_clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Determine the logo path (fall back to default if none set).
    logo_path = await get_logo_path(chat_id) or DEFAULT_LOGO_IMAGE
    if not os.path.exists(logo_path):
        raise RuntimeError(f"Logo not found: {logo_path}")

    # Load the logo and resize it to fit the top-right corner.
    logo_clip = ImageClip(logo_path)
    logo_height = int(VIDEO_HEIGHT * LOGO_MAX_HEIGHT_RATIO)
    logo_clip = logo_clip.resize(height=logo_height)
    logo_clip = logo_clip.set_position((VIDEO_WIDTH - logo_clip.w - LOGO_MARGIN_PX, LOGO_MARGIN_PX))

    # Find the first available font.
    font_path = None
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            font_path = candidate
            break
    if not font_path:
        raise RuntimeError("No suitable font found")

    # Calculate the duration of each subtitle segment.
    total_audio_duration = audio_clip.duration
    segment_duration = total_audio_duration / len(segments)

    # Create the text clips for each segment.
    text_clips = []
    for i, segment in enumerate(segments):
        start_time = i * segment_duration
        end_time = start_time + segment_duration

        # Create a text clip with the segment text.
        text_clip = TextClip(
            segment,
            fontsize=48,
            font=font_path,
            color="white",
            bg_color="rgba(0,0,0,0.6)",
            size=(VIDEO_WIDTH * SUBTITLE_MAX_WIDTH_RATIO, None),
            method="caption",
        ).set_duration(segment_duration)

        # Position the text clip at the center of the video.
        text_clip = text_clip.set_position("center").set_start(start_time)
        text_clips.append(text_clip)

    # Composite all the clips together.
    final_clip = CompositeVideoClip([
        bg_clip,
        *text_clips,
        logo_clip,
    ]).set_duration(total_audio_duration)

    # Set the audio.
    final_clip = final_clip.set_audio(audio_clip)

    # Write the final video to the output path.
    final_clip.write_videofile(
        output_path,
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast",
    )

    # Clean up the temporary audio file.
    try:
        os.remove(tmp_audio.name)
    except OSError:
        pass