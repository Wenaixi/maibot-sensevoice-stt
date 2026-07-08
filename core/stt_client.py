"""SenseVoice HTTP 客户端 — 对接本地 Docker sidecar。"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field

import aiohttp


@dataclass
class TranscriptionResult:
    """转录结果。

    Attributes:
        text: 转录文本（失败时为空字符串）。
        success: 是否成功。
        error_type: 失败原因分类
            (``"timeout"`` / ``"connection"`` / ``"http_error"`` / ``None``)。
        attempt: 实际尝试次数。
    """

    text: str
    success: bool
    error_type: str | None = None
    attempt: int = 1

    @classmethod
    def ok(cls, text: str, attempt: int = 1) -> TranscriptionResult:
        return cls(text=text.strip(), success=True, attempt=attempt)

    @classmethod
    def fail(cls, error_type: str, attempt: int = 1) -> TranscriptionResult:
        return cls(text="", success=False, error_type=error_type, attempt=attempt)


class SenseVoiceClient:
    """本地 SenseVoice sidecar 的异步 HTTP 客户端。

    向 ``POST {endpoint_url}`` 发送 multipart/form-data 请求，
    字段 ``file``（WAV 音频）和 ``language``（语言标签）。

    内置最多 **2 次重试**（间隔 1s），应对瞬时网络抖动。
    """

    _MAX_RETRIES = 2
    _RETRY_DELAY = 1.0

    def __init__(self, endpoint_url: str, timeout: float, language: str) -> None:
        self._endpoint = endpoint_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._language = language

    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        """发送音频到 SenseVoice sidecar，返回转录结果。

        Args:
            audio_path: 本地 WAV 文件的绝对路径。

        Returns:
            TranscriptionResult：成功时 ``text`` 包含转录文本，
            失败时 ``text`` 为空且 ``error_type`` 指示原因。
        """
        filename = os.path.basename(audio_path)

        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                result = await self._post_transcribe(audio_path, filename)
                if result.success:
                    result.attempt = attempt
                    return result
                if result.error_type == "http_error":
                    return result  # 非 200 不重试
            except asyncio.TimeoutError:
                if attempt < self._MAX_RETRIES:
                    await asyncio.sleep(self._RETRY_DELAY)
                    continue
                return TranscriptionResult.fail("timeout", attempt)
            except aiohttp.ClientConnectorError:
                if attempt < self._MAX_RETRIES:
                    await asyncio.sleep(self._RETRY_DELAY)
                    continue
                return TranscriptionResult.fail("connection", attempt)
            except Exception:
                return TranscriptionResult.fail("unknown", attempt)

            if attempt < self._MAX_RETRIES:
                await asyncio.sleep(self._RETRY_DELAY)

        return TranscriptionResult.fail("timeout", self._MAX_RETRIES)

    async def _post_transcribe(
        self, audio_path: str, filename: str
    ) -> TranscriptionResult:
        """单次 POST 请求，不重试。"""
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                with open(audio_path, "rb") as audio_file:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        audio_file,
                        filename=filename,
                        content_type="audio/wav",
                    )
                    data.add_field("language", self._language)
                    async with session.post(self._endpoint, data=data) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            text = (result.get("text") or "").strip()
                            return TranscriptionResult.ok(text)
                        return TranscriptionResult.fail("http_error")
        except Exception:
            raise
