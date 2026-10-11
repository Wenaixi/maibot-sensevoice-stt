# dmjxmj sensevoice-stt

## 官方上游与版本溯源
- 官方仓库（Upstream Repository）：https://github.com/DMJXMJ/maibot-sensevoice-stt
- 官方作者（Author / Maintainer）：DMJXMJ
- 功能定位：SenseVoice 语音识别（STT）转文字插件
- 本地演进定位：基于官方上游最新版本，融入本地生产环境兼容性定制与稳定性加固。
- 本地专属定制：本地跟踪完整 sidecar 与云端端点，配置 SiliconFlow 高精度转写通道。


## 插件基本信息

- 插件 ID：`dmjxmj.sensevoice-stt`
- 频率：low
- 描述：硅基流动 SenseVoice STT（语音转文本）

## 主要功能 / 配置要点

- http://localhost:50000 默认
- 测试用
- 3 tests

## 接入依赖

- MaiBot SDK 2.x（`MaiBotPlugin` 基类 + `Action`/`Command`/`HookHandler`）
- 容器内一律用服务名（`napcat` / `core`），禁止 `127.0.0.1`
- 配置通过 `PluginConfigBase`（Pydantic v2）

## 关键日志（启动标志）

插件加载时输出 `xxx 已加载`。如未加载，参考 MaiBot 启动日志 `已加载=N 失败=M 未激活=K`。

## 用法

由 MaiBot LLM 自主调用或通过命令触发。详见 plugin 文档或上游 README。

## 历史脚注

- 2026-08-15：自动生成（深度 plan B10）
- 本仓库是主人本地副本，服务器 `/MaiBot/plugins/` 是 runtime。
- 修改走工作流（本机改 → 本机 commit → 部署服务器 → 验证加载）。
