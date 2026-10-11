# MaiBot SenseVoice 语音识别转文字插件 (maibot-sensevoice-stt)

基于阿里达摩院 SenseVoice 语音基础大模型的 MaiBot 离线与云端语音识别（STT）插件。支持高精度识别 QQ 群聊与私聊语音消息，具备极速多语言识别、声音事件检测（如笑声、掌声、咳嗽）与情绪感知能力。

## 核心技术架构

1. 语音监听：捕获 OneBot 入站 `record` 语音消息段并拉取音频原始二进制数据。
2. 音频预处理：内置音频转换管道，自动将 silk / amr / mp3 统一重采样转码为 16kHz 16bit 单声道 WAV 格式。
3. 双模识别引擎：
   - 本地/容器 Sidecar 模式：连接部署在同一网络下的 SenseVoice 独立推理服务容器。
   - 云端高速 API 模式：支持对接 SiliconFlow、ModelScope 等兼容 OpenAI Audio 规范的第三方托管接口。
4. 上下文合成：将语音转写文本直接注入到 MaiBot 的聊天上下文流中，使麦麦能够像阅读文字一样“听懂”语音。

## 配置项详解

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `[plugin].enabled` | bool | `true` | 是否启用语音识别插件 |
| `[stt].backend` | string | `"sidecar"` | 推理后端类型：`"sidecar"` 或 `"cloud_api"` |
| `[stt].api_url` | string | `"http://sensevoice:8000/v1/audio/transcriptions"` | 识别服务端点 URL |
| `[stt].api_key` | string | `""` | 云端接口访问密钥（本地 Sidecar 留空） |
| `[stt].language` | string | `"auto"` | 目标语言：`"auto"`、`"zh"`、`"en"`、`"ja"`、`"yue"` |
| `[stt].timeout_seconds` | int | `20` | 单条语音转写硬超时限制（秒） |

## 开源协议

本项目采用 MIT 许可证开源，详情请参阅 [LICENSE](LICENSE)。
