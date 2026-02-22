"""Text-to-speech tool using edge-tts."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.tools.base import Tool


def _get_proxy() -> str | None:
    """Get proxy from environment variables."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or \
           os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")


# 中文语音列表
CHINESE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓 - 女声，自然
    "yunxi": "zh-CN-YunxiNeural",            # 云希 - 男声，自然
    "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓伊 - 女声，活泼
    "yunjian": "zh-CN-YunjianNeural",        # 云健 - 男声，新闻
    "xiaoxuan": "zh-CN-XiaoxuanNeural",      # 晓萱 - 女声，温柔
    "yunxia": "zh-CN-YunxiaNeural",          # 云夏 - 男声，儿童
    "xiaochen": "zh-CN-XiaochenNeural",      # 晓辰 - 女声，客服
    "xiaohan": "zh-CN-XiaohanNeural",        # 晓涵 - 女声，温柔
    "xiaomeng": "zh-CN-XiaomengNeural",      # 晓梦 - 女声，可爱
    "xiaomo": "zh-CN-XiaomoNeural",          # 晓墨 - 女声，自然
    "xiaoqiu": "zh-CN-XiaoqiuNeural",        # 晓秋 - 女声，知性
    "xiaorui": "zh-CN-XiaoruiNeural",        # 晓睿 - 女声，客服
    "xiaoshuang": "zh-CN-XiaoshuangNeural",  # 晓双 - 女声，儿童
    "xiaoxuan2": "zh-CN-XiaoxuanNeural",     # 晓萱 - 女声，温柔
    "xiaoyan": "zh-CN-XiaoyanNeural",        # 晓颜 - 女声，自然
    "xiaoyou": "zh-CN-XiaoyouNeural",        # 晓悠 - 女声，儿童
    "yunfeng": "zh-CN-YunfengNeural",        # 云枫 - 男声，自然
    "yunhao": "zh-CN-YunhaoNeural",          # 云皓 - 男声，新闻
    "yunxiang": "zh-CN-YunxiangNeural",      # 云翔 - 男声，自然
    "yunyang": "zh-CN-YunyangNeural",        # 云扬 - 男声，新闻
}

# 英语语音列表
ENGLISH_VOICES = {
    "aria": "en-US-AriaNeural",          # 女声，自然
    "michelle": "en-US-MichelleNeural",  # 女声，自然
    "guy": "en-US-GuyNeural",            # 男声，自然
    "sonia": "en-GB-SoniaNeural",        # 女声，英式
    "ryan": "en-GB-RyanNeural",          # 男声，英式
}

# 所有可用语音
ALL_VOICES = {**CHINESE_VOICES, **ENGLISH_VOICES}


class TTSTool(Tool):
    """Text-to-speech tool using Microsoft Edge TTS."""

    def __init__(self, output_dir: Path | None = None, proxy: str | None = None):
        self._output_dir = output_dir or Path.home() / ".nanobot" / "tts"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._proxy = proxy

    @property
    def name(self) -> str:
        return "tts"

    @property
    def description(self) -> str:
        return (
            "Convert text to speech audio. "
            "Returns the path to the generated audio file. "
            "Use this to generate voice output from text."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to convert to speech"
                },
                "voice": {
                    "type": "string",
                    "description": (
                        "Voice name. Chinese: xiaoxiao, yunxi, xiaoyi, yunjian, xiaoxuan. "
                        "English: aria, michelle, guy, sonia, ryan. "
                        "Default: xiaoxiao (Chinese female)"
                    ),
                    "enum": list(ALL_VOICES.keys()),
                    "default": "xiaoxiao"
                },
                "rate": {
                    "type": "string",
                    "description": (
                        "Speech rate adjustment. "
                        "Examples: '+10%' (faster), '-10%' (slower), '+0%' (normal)"
                    ),
                    "default": "+0%"
                },
                "pitch": {
                    "type": "string",
                    "description": (
                        "Pitch adjustment. "
                        "Examples: '+10Hz' (higher), '-10Hz' (lower), '+0Hz' (normal)"
                    ),
                    "default": "+0Hz"
                }
            },
            "required": ["text"]
        }

    async def execute(
        self,
        text: str,
        voice: str = "xiaoxiao",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        **kwargs: Any
    ) -> str:
        """Convert text to speech and return the audio file path."""
        try:
            import edge_tts
        except ImportError:
            return "Error: edge-tts not installed. Run: pip install edge-tts"

        # 获取完整语音名称
        voice_name = ALL_VOICES.get(voice, CHINESE_VOICES["xiaoxiao"])

        # 生成文件名：tts_年月日_时分秒.mp3
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}.mp3"
        output_path = self._output_dir / filename

        # 获取代理配置
        proxy = self._proxy or _get_proxy()

        try:
            communicate = edge_tts.Communicate(
                text,
                voice_name,
                rate=rate,
                pitch=pitch,
                proxy=proxy
            )
            await communicate.save(str(output_path))
            logger.info("TTS generated: {} -> {}", text[:50], output_path)
            return f"Audio generated: {output_path}"
        except Exception as e:
            logger.error("TTS failed: {}", e)
            error_msg = str(e)
            if "403" in error_msg or "Invalid response status" in error_msg:
                return (
                    "Error: Cannot connect to Microsoft TTS service. "
                    "Please set HTTPS_PROXY environment variable, e.g., "
                    "set HTTPS_PROXY=http://127.0.0.1:7890"
                )
            return f"Error generating speech: {error_msg}"


class ListVoicesTool(Tool):
    """Tool to list available TTS voices."""

    @property
    def name(self) -> str:
        return "list_voices"

    @property
    def description(self) -> str:
        return "List available text-to-speech voices."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Filter by language: 'chinese', 'english', or 'all'",
                    "enum": ["chinese", "english", "all"],
                    "default": "all"
                }
            }
        }

    async def execute(self, language: str = "all", **kwargs: Any) -> str:
        """Return a formatted list of available voices."""
        if language == "chinese":
            voices = CHINESE_VOICES
            header = "Chinese Voices (zh-CN):"
        elif language == "english":
            voices = ENGLISH_VOICES
            header = "English Voices:"
        else:
            voices = ALL_VOICES
            header = "Available Voices:"

        lines = [header, ""]
        for name, voice_id in voices.items():
            lines.append(f"  {name}: {voice_id}")

        return "\n".join(lines)
