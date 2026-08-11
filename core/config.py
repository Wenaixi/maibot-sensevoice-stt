"""SenseVoice STT 插件 — Pydantic 配置模型。"""

from maibot_sdk import Field, PluginConfigBase


class PluginSection(PluginConfigBase):
    """插件基础配置，对应 config.toml 的 [plugin] 节。"""

    __ui_label__ = "插件设置"
    __ui_icon__ = "settings"
    __ui_order__ = 0

    enabled: bool = Field(
        default=True,
        description="是否启用语音转文字",
        json_schema_extra={"group": "plugin"},
    )
    config_version: str = Field(
        default="0.3.0",
        description="配置版本",
        json_schema_extra={"group": "plugin"},
    )


class SttConfig(PluginConfigBase):
    """STT 后端配置。"""

    __ui_label__ = "SenseVoice 后端"
    __ui_icon__ = "record_voice_over"
    __ui_order__ = 10

    endpoint_url: str = Field(
        default="https://api.siliconflow.cn/v1/audio/transcriptions",
        description=(
            "转录接口地址。硅基流动: "
            "https://api.siliconflow.cn/v1/audio/transcriptions"
        ),
        json_schema_extra={
            "placeholder": "https://api.siliconflow.cn/v1/audio/transcriptions",
            "group": "stt",
        },
    )
    api_key: str = Field(
        default="",
        description="API Key（硅基流动）",
        json_schema_extra={
            "placeholder": "sk-xxx",
            "group": "stt",
        },
    )
    model: str = Field(
        default="FunAudioLLM/SenseVoiceSmall",
        description="模型名称",
        json_schema_extra={
            "placeholder": "FunAudioLLM/SenseVoiceSmall",
            "group": "stt",
        },
    )
    timeout_seconds: int = Field(
        default=30,
        description="转录请求超时（秒）",
        json_schema_extra={"placeholder": "30", "group": "stt"},
    )
    language: str = Field(
        default="auto",
        description="识别语言 (auto/zh/en/yue/ja/ko)",
        json_schema_extra={"placeholder": "auto", "group": "stt"},
    )


class SenseVoiceSttPluginConfig(PluginConfigBase):
    """插件根配置。"""

    plugin: PluginSection = Field(default_factory=PluginSection)
    stt: SttConfig = Field(default_factory=SttConfig)
