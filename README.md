# maibot-sensevoice-stt

麦麦（MaiBot）SenseVoice 语音识别 STT 插件

## 插件信息

版本：0.2.0
分类：工具
图标：🎙️
插件 ID：dmjxmj.sensevoice-stt

## 功能

transcribe_voice_segments：在消息到达 LLM 前拦截语音段，调用本地 SenseVoice sidecar 转录为文字并原地替换为文本段。支持多段语音并发转录，单段时无额外开销。sidecar 不可用时静默降级为 `[voice]` 占位符，不阻断消息流。
sensevoice_stt_status：WebUI 首页状态卡片，显示启用状态、运行时间、总请求数、成功率、连续失败次数等实时统计。连续失败 ≥3 次时写入 WARNING 日志。

## 安装

1. **部署 SenseVoice sidecar**：见 [sidecar/README.md](sidecar/README.md)。Maibot-Napcat 环境执行 `docker compose up -d sensevoice`，然后 `curl -sS http://127.0.0.1:50000/health` 确认 ready。
2. **拷贝插件到 MaiBot 插件目录**：
   ```bash
   sudo cp -r plugin-src/sensevoice-stt/ data/MaiMBot/plugins/dmjxmj.sensevoice-stt/
   ```
3. **重启 MaiBot core**：
   ```bash
   docker compose restart core
   ```

## 配置

默认配置位于 `config.toml`。

- `plugin.enabled`：是否启用语音转文字。
- `plugin.config_version`：插件配置版本，当前为 `"0.2.0"`。
- `stt.endpoint_url`：SenseVoice sidecar 转录接口地址（默认 `http://sensevoice:50000/v1/audio/transcriptions`）。
- `stt.timeout_seconds`：转录请求超时，单位为秒（默认 30）。
- `stt.language`：识别语言，支持 `auto` / `zh` / `en` / `yue` / `ja` / `ko`（默认 `"auto"`）。

修改 `config.toml` 后，MaiBot 会自动调用 `on_config_update()` 应用新配置，无需手动重启。

## 隐私与安全

- **转录文本不记日志**：sidecar 和插件日志仅记录 `text_length`（字符数），不记录完整文本内容。
- **本地处理**：音频文件仅在 Docker 内部网络传输，不上传任何云端服务。
- **临时文件清理**：转录完成后立即删除临时 WAV 文件。

## 已知限制

- 仅处理入站消息的 voice segment，不涉及 TTS 输出。
- sidecar 不可用时，转录静默失败，voice segment 回退为 `[voice]` 占位符。
- SenseVoiceSmall 模型仅支持中文、英文、粤语、日语、韩语。

## 许可证

MIT
