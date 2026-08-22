"""Unified Volcengine Ark plugin for Hermes.

This root module is imported by Hermes' plugin loader. The provider modules are
kept separate so Ark can be maintained independently from Hermes core.
"""

from __future__ import annotations


def register(ctx) -> None:
    """Register Ark providers and override understanding tools.

    Provider implementations live in separate modules so the plugin can be
    maintained independently from Hermes core.
    """
    from .providers.image_generate import ArkImageGenerateProvider
    from .providers.text_to_speech import ArkTextToSpeechProvider
    from .providers.transcribe_audio import ArkTranscribeAudioProvider
    from .providers.video_generate import ArkVideoGenerateProvider
    from .common.config import configure_context
    from .tools.vision_analyze import VISION_ANALYZE_SCHEMA, ark_vision_analyze, check_ark_vision
    from .tools.video_analyze import VIDEO_ANALYZE_SCHEMA, ark_video_analyze, check_ark_video

    configure_context(ctx)
    ctx.register_tts_provider(ArkTextToSpeechProvider())
    ctx.register_transcription_provider(ArkTranscribeAudioProvider())
    ctx.register_image_gen_provider(ArkImageGenerateProvider())
    ctx.register_video_gen_provider(ArkVideoGenerateProvider())

    # Understanding has no provider registry in Hermes v0.20.x. Keep the four
    # provider-backed capabilities available even when override consent was
    # declined, and only replace the two understanding tools when authorized.
    if not ctx.has_capability("tools.override"):
        return

    import importlib
    importlib.import_module("tools.vision_tools")
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
