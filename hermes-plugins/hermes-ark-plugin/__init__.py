"""Unified Volcengine Ark plugin for Hermes.

This root module is imported by Hermes' plugin loader. The provider modules are
kept separate so Ark can be maintained independently from Hermes core.
"""

from __future__ import annotations

import importlib


def register(ctx) -> None:
    """Register Ark providers and override understanding tools.

    Provider implementations live in separate modules so the plugin can be
    maintained independently from Hermes core.
    """
    from .providers.image_generate import ArkImageGenerateProvider
    from .providers.text_to_speech import ArkTextToSpeechProvider
    from .providers.transcribe_audio import ArkTranscribeAudioProvider
    from .providers.video_generate import ArkVideoGenerateProvider
    from .tools.transcribe_audio import TRANSCRIBE_AUDIO_SCHEMA, ark_transcribe_audio, check_ark_transcribe_audio
    from .tools.vision_analyze import VISION_ANALYZE_SCHEMA, ark_vision_analyze, check_ark_vision
    from .tools.video_analyze import VIDEO_ANALYZE_SCHEMA, ark_video_analyze, check_ark_video

    ctx.register_tts_provider(ArkTextToSpeechProvider())
    ctx.register_transcription_provider(ArkTranscribeAudioProvider())
    ctx.register_image_gen_provider(ArkImageGenerateProvider())
    ctx.register_video_gen_provider(ArkVideoGenerateProvider())

    # Some Hermes entrypoints discover plugins before importing model_tools.
    # Preload the built-in understanding tools so Ark's same-name overrides
    # are registered last and cannot be reclaimed by a later built-in import.
    importlib.import_module("tools.vision_tools")

    ctx.register_tool(
        name="transcribe_audio",
        toolset="tts",
        schema=TRANSCRIBE_AUDIO_SCHEMA,
        handler=ark_transcribe_audio,
        check_fn=check_ark_transcribe_audio,
        emoji="🎙️",
        override=True,
    )
    ctx.register_tool(
        name="vision_analyze",
        toolset="vision",
        schema=VISION_ANALYZE_SCHEMA,
        handler=ark_vision_analyze,
        check_fn=check_ark_vision,
        is_async=True,
        emoji="👁️",
        override=True,
    )
    ctx.register_tool(
        name="video_analyze",
        toolset="video",
        schema=VIDEO_ANALYZE_SCHEMA,
        handler=ark_video_analyze,
        check_fn=check_ark_video,
        is_async=True,
        emoji="🎬",
        override=True,
    )
