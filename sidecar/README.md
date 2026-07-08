# SenseVoice STT Sidecar — 独立部署

SenseVoice 语音转文字 Docker 容器，基于 FunASR SenseVoiceSmall 模型。

支持语言：中文 / 英文 / 粤语 / 日语 / 韩语（自动检测）。

## 快速启动

### 构建镜像

```bash
cd plugin-src/sensevoice-stt/sidecar
docker build -t sensevoice-stt:latest .
```

### 启动容器

```bash
docker run -d \
  --name sensevoice-stt \
  -p 127.0.0.1:50000:50000 \
  -v sensevoice-models:/models \
  --memory 2g \
  sensevoice-stt:latest
```

首次启动时自动从 ModelScope 下载模型（约 1GB），缓存在 `sensevoice-models` volume 中。

### 检查就绪

```bash
curl -sS http://127.0.0.1:50000/health
# → {"status":"ready"}
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查，返回 `{"status":"ready"}` |
| `/v1/audio/transcriptions` | POST | 语音转文字 |

### POST /v1/audio/transcriptions

**Content-Type**：`multipart/form-data`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | file | 是 | — | 音频文件（WAV/MP3/OGG/FLAC） |
| `language` | string | 否 | `auto` | 语言：`auto`/`zh`/`en`/`yue`/`ja`/`ko` |

**响应**：

```json
{"text": "转录文本"}
```

**示例**：

```bash
curl -sS -F "file=@audio.wav" -F "language=auto" \
  http://127.0.0.1:50000/v1/audio/transcriptions
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODELSCOPE_CACHE` | `/models` | 模型缓存目录 |

## GPU 加速（可选）

默认使用 CPU 推理（约 2GB RAM）。如需 GPU 加速：

```dockerfile
# 将 Dockerfile 中的 torch 改为 CUDA 版本
RUN pip install torch==2.6.0+cu118 torchaudio==2.6.0+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# 修改 server.py 中的 device 参数
model = AutoModel(model="iic/SenseVoiceSmall", device="cuda")
```

启动时添加 `--gpus all`：

```bash
docker run -d --gpus all --name sensevoice-stt ...
```

## 内存占用

| 配置 | 模型大小 | 运行时内存 |
|------|---------|-----------|
| CPU（默认） | ~1GB（磁盘） | ~1.5-2GB RAM |
| GPU | ~1GB（磁盘） | ~1GB VRAM |

## License

MIT — 与父插件 `sensevoice-stt` 一致。
