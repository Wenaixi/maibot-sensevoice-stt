"""SenseVoice STT 插件 — Pydantic 配置模型。"""

from maibot_sdk import Field, PluginConfigBase


class PluginSection(PluginConfigBase):
    """插件基础配置，对应 config.toml 的 [plugin] 节。"""

    enabled: bool = Field(default=True, description="是否启用语音转文字")
    config_version: str = Field(default="0.2.0", description="配置版本")


class SttConfig(PluginConfigBase):
    """STT 后端配置。"""

    endpoint_url: str = Field(
        default="http://sensevoice:50000/v1/audio/transcriptions",
        description="SenseVoice API 地址",
    )
    timeout_seconds: int = Field(default=30, description="请求超时（秒）")
    language: str = Field(
        default="auto", description="识别语言 (auto/zh/en/yue/ja/ko)"
    )


class SenseVoiceSttPluginConfig(PluginConfigBase):
    """插件根配置。"""

    plugin: PluginSection = Field(default_factory=PluginSection)
    stt: SttConfig = Field(default_factory=SttConfig)
