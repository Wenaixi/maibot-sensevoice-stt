"""SenseVoice STT 插件 — 将 QQ 语音消息转录为文字。

通过 ``@HookHandler("chat.receive.before_process")`` 在消息到达 LLM 之前
拦截语音段，调用本地 SenseVoice Docker sidecar 转录，原地替换为文本段，
并重建 ``processed_plain_text``。

纯本地方案：不依赖任何第三方云 API。
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from maibot_sdk import HomeCard, HookHandler, MaiBotPlugin
from maibot_sdk.types import ErrorPolicy, HookMode, HookOrder

from .core.audio_utils import cleanup_temp_file, decode_base64_to_wav
from .core.config import SenseVoiceSttPluginConfig
from .core.stt_client import SenseVoiceClient, TranscriptionResult


class SenseVoiceSttPlugin(MaiBotPlugin):
    """SenseVoice STT 插件主类。"""

    config_model = SenseVoiceSttPluginConfig

    _MAX_CONSECUTIVE_FAIL_LOG = 3  # 连续失败达此阈值时记 WARNING

    def __init__(self) -> None:
        super().__init__()
        self._client: SenseVoiceClient | None = None
        self._stats: dict[str, int] = {}
        self._started_at: float = 0.0
        self._reset_stats()

    def _reset_stats(self) -> None:
        self._stats = {
            "total_requests": 0,
            "total_success": 0,
            "total_failure": 0,
            "consecutive_failures": 0,
        }
        self._started_at = time.time()

    # ===== 生命周期（SDK 强制）=====

    async def on_load(self) -> None:
        self._init_client()
        self._reset_stats()
        self.ctx.logger.info(
            "SenseVoice STT 插件已加载，后端: %s",
            self.config.stt.endpoint_url,
        )

    async def on_unload(self) -> None:
        self._client = None
        self.ctx.logger.info("SenseVoice STT 插件已卸载")

    async def on_config_update(
        self, scope: str, config_data: dict, version: str
    ) -> None:
        if scope == "self":
            self._init_client()
            self.ctx.logger.info("SenseVoice STT 配置已更新 (version=%s)", version)

    # ===== 内部 =====

    def _init_client(self) -> None:
        if self.config.plugin.enabled:
            self._client = SenseVoiceClient(
                endpoint_url=self.config.stt.endpoint_url,
                timeout=self.config.stt.timeout_seconds,
                language=self.config.stt.language,
            )
        else:
            self._client = None

    def _record_transcription(self, result: TranscriptionResult) -> None:
        self._stats["total_requests"] += 1
        if result.success:
            self._stats["total_success"] += 1
            self._stats["consecutive_failures"] = 0
        else:
            self._stats["total_failure"] += 1
            self._stats["consecutive_failures"] += 1
            if self._stats["consecutive_failures"] == self._MAX_CONSECUTIVE_FAIL_LOG:
                self.ctx.logger.warning(
                    "SenseVoice STT 连续失败 %d 次 (type=%s)",
                    self._stats["consecutive_failures"],
                    result.error_type,
                )

    def _uptime_hours(self) -> float:
        return (time.time() - self._started_at) / 3600.0

    # ===== HookHandler =====

    @HookHandler(
        "chat.receive.before_process",
        name="sensevoice_stt_transcriber",
        description="将语音消息段转录为文字",
        mode=HookMode.BLOCKING,
        order=HookOrder.EARLY,
        timeout_ms=30000,
        error_policy=ErrorPolicy.SKIP,
    )
    async def transcribe_voice_segments(
        self, message: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any] | None:
        """拦截入站消息，将 voice 段转录为 text 段。

        Hook 参数由 ``chat.receive.before_process`` 注入，
        ``message`` 包含 ``raw_message``（段列表）和
        ``processed_plain_text``（纯文本表示）。
        """
        if not self._client or not message:
            return None
        raw = message.get("raw_message")
        if not isinstance(raw, list):
            return None

        modified = False
        voice_count = 0
        transcribed_count = 0
        runtime_dir = self.ctx.paths.runtime_dir

        # ---- 收集语音段 ----
        voice_tasks: list[tuple[int, dict[str, Any], str]] = []
        for i, seg in enumerate(raw):
            if not isinstance(seg, dict) or seg.get("type") != "voice":
                continue
            voice_count += 1
            b64 = seg.get("binary_data_base64", "")
            if not b64:
                self.ctx.logger.warning(
                    "SenseVoice STT 跳过 voice 段: missing_binary_data"
                )
                continue
            tmp = decode_base64_to_wav(b64, runtime_dir)
            voice_tasks.append((i, seg, tmp))

        async def _transcribe_one(idx: int, seg: dict, tmp: str):
            try:
                result = await self._client.transcribe(tmp)
                return idx, seg, result
            finally:
                cleanup_temp_file(tmp)

        if voice_tasks:
            # 单段直达；多段并发
            if len(voice_tasks) == 1:
                outcomes = [await _transcribe_one(*voice_tasks[0])]
            else:
                outcomes = await asyncio.gather(
                    *[_transcribe_one(i, s, t) for i, s, t in voice_tasks]
                )

            for idx, seg, result in outcomes:
                self._record_transcription(result)
                if result.success:
                    seg.clear()
                    seg["type"] = "text"
                    seg["data"] = result.text
                    modified = True
                    transcribed_count += 1
                    self.ctx.logger.info(
                        "SenseVoice STT 转录成功: text_length=%d",
                        len(result.text),
                    )
                else:
                    self.ctx.logger.warning(
                        "SenseVoice STT 转录失败: error=%s attempt=%d",
                        result.error_type,
                        result.attempt,
                    )

        if modified:
            message["processed_plain_text"] = rebuild_plain_text(raw)
            message["display_message"] = message["processed_plain_text"]
            self.ctx.logger.info(
                "SenseVoice STT 已更新消息: voice_segments=%d transcribed=%d",
                voice_count,
                transcribed_count,
            )
            return {"action": "continue", "modified_kwargs": {"message": message}}

        return None

    # ===== HomeCard =====

    @HomeCard(
        name="sensevoice_stt_status",
        title="语音转文字状态",
        content="SenseVoice STT 插件运行状态与统计",
        icon="\U0001F399",
        width="half",
        order=100,
    )
    async def stt_home_card(self) -> dict[str, Any]:
        s = self._stats
        enabled = "启用" if self._client else "已禁用"
        uptime_h = self._uptime_hours()
        rate_str = ""
        if s["total_requests"] > 0:
            rate = s["total_success"] / s["total_requests"] * 100
            rate_str = f"{rate:.1f}%"
        else:
            rate_str = "N/A"

        return {
            "blocks": [
                {
                    "type": "key_value",
                    "items": [
                        {"key": "状态", "value": enabled},
                        {"key": "运行时间", "value": f"{uptime_h:.1f}h"},
                        {"key": "总请求", "value": str(s["total_requests"])},
                        {"key": "成功", "value": str(s["total_success"])},
                        {"key": "失败", "value": str(s["total_failure"])},
                        {"key": "成功率", "value": rate_str},
                        {"key": "连续失败", "value": str(s["consecutive_failures"])},
                    ],
                }
            ]
        }


def rebuild_plain_text(segments: list[dict[str, Any]]) -> str:
    """从段列表重建纯文本表示。

    与 ``adapter/codecs/inbound/text.py:build_plain_text`` 逻辑对齐，
    确保 LLM 收到的文本格式一致。
    """
    parts: list[str] = []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        t = seg.get("type", "")
        if t == "text":
            parts.append(str(seg.get("data", "")))
        elif t == "voice":
            parts.append("[voice]")
        elif t == "image":
            parts.append("[image]")
        elif t == "reply":
            parts.append("[reply]")
    text = "".join(parts).strip()
    return text or "[unsupported]"


def create_plugin() -> SenseVoiceSttPlugin:
    """MaiBot 插件入口工厂函数（SDK 强制要求）。"""
    return SenseVoiceSttPlugin()
