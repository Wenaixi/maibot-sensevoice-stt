"""SenseVoice HTTP 客户端 — 对接硅基流动 FunAudioLLM/SenseVoiceSmall API。"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

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


@dataclass
class HealthCheckResult:
    """SenseVoice sidecar 健康检查结果。"""

    ok: bool
    status: str
    error_type: str | None = None

    @classmethod
    def ready(cls) -> HealthCheckResult:
        return cls(ok=True, status="ready")

    @classmethod
    def fail(cls, error_type: str, status: str = "unreachable") -> HealthCheckResult:
        return cls(ok=False, status=status, error_type=error_type)


def build_health_url(endpoint_url: str) -> str:
    """从转录 endpoint 推导 health endpoint（硅基流动不需要，保持兼容）。"""
    endpoint = endpoint_url.rstrip("/")
    parsed = urlsplit(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return f"{endpoint}/health"

    path = parsed.path.rstrip("/")
    suffix = "/v1/audio/transcriptions"
    if path.endswith(suffix):
        path = path[: -len(suffix)]
    health_path = f"{path}/health" if path else "/health"
    return urlunsplit((parsed.scheme, parsed.netloc, health_path, "", ""))


class SenseVoiceClient:
    """硅基流动 FunAudioLLM/SenseVoiceSmall API 的异步 HTTP 客户端。

    向 ``POST {endpoint_url}`` 发送 multipart/form-data 请求，
    字段 ``file``（WAV 音频）、``language``（语言标签）和 ``model``（模型名称）。
    认证通过 ``Authorization: Bearer <api_key>`` 头传递。

    内置最多 **2 次重试**（间隔 1s），应对瞬时网络抖动。
    """

    _MAX_RETRIES = 2
    _RETRY_DELAY = 1.0

    def __init__(self, endpoint_url: str, timeout: float, language: str, api_key: str = "", model: str = "FunAudioLLM/SenseVoiceSmall") -> None:
        self._endpoint = endpoint_url.rstrip("/")
        self._timeout_seconds = float(timeout)
        self._timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        self._health_timeout = aiohttp.ClientTimeout(total=min(self._timeout_seconds, 3.0))
        self._language = language
        self._api_key = api_key
        self._model = model
        self._health_url = build_health_url(self._endpoint)

    @property
    def endpoint_url(self) -> str:
        return self._endpoint

    @property
    def health_url(self) -> str:
        return self._health_url

    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        """发送音频到硅基流动 API，返回转录结果。

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
                headers = {}
                if self._api_key:
                    headers["Authorization"] = f"Bearer {self._api_key}"

                with open(audio_path, "rb") as audio_file:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        audio_file,
                        filename=filename,
                        content_type="audio/wav",
                    )
                    data.add_field("language", self._language)
                    data.add_field("model", self._model)
                    async with session.post(self._endpoint, data=data, headers=headers) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            # 硅基流动返回格式: {"text": "转录文本"}
                            text = (result.get("text") or "").strip()
                            return TranscriptionResult.ok(text)
                        # 错误处理
                        error_text = await resp.text()
                        return TranscriptionResult.fail(f"http_error_{resp.status}")
        except Exception:
            raise

    async def check_health(self) -> HealthCheckResult:
        """检查 API 连接状态（硅基流动 无 health 接口，返回模拟状态）。"""
        # 硅基流动 API 没有 health 端点，直接返回 ready
        # 实际健康检查会在首次转录时发现
        return HealthCheckResult.ready()
