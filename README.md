# Cursor OpenAI Bridge

[English](README.en.md)

基于 **Python（FastAPI）** 实现的本地 OpenAI 兼容代理，配合 **ngrok** 内网穿透，让 **Cursor** 能稳定使用多家 **OpenAI 兼容中转**（OpenRouter、九天 MoMA、One API 等）。

它主要解决三类问题：Cursor 不接受带 `/` 的模型名、上游 API 路径与 Cursor 默认 `/v1` 不一致、以及 Cursor 云端无法访问本机 `127.0.0.1`。代理负责**模型别名映射**、**请求路径转发**，并通过 ngrok 提供公网入口。

运行配置集中在根目录 [`config.yaml`](config.yaml)，切换上游或模型时只需修改该文件。

## 解决的问题

| Cursor 限制 | 代理处理方式 |
|-------------|----------------|
| 不接受 `provider/model` 等含 `/` 的模型名 | `model_aliases` 别名映射 |
| 上游路径非标准 `/v1/chat/completions` | 可配置 `chat_path` |
| 无法访问 `127.0.0.1` | 经 **ngrok** 暴露为公网 HTTPS |

## 环境要求

- Python 3.10+
- [ngrok](https://ngrok.com/)
- Cursor Pro+（自定义 OpenAI 兼容模型）

## 配置修改（`config.yaml`）

### 切换模型

编辑 `model_aliases`：**左侧**为 Cursor 自定义模型名，**右侧**为上游真实 id。

```yaml
model_aliases:
  GLM-5.1: "z.ai/glm-5.1"
  # deepseek-v4-flash: "deepseek/deepseek-v4-flash"   # 注释即停用
  qwen3.5-27b: "qwen/qwen3.5-27b"
```

在 Cursor 中添加/选择与**左侧**同名的模型。修改后执行 `stop` + `start` 重启代理。

### 切换上游中转

编辑 `provider` 与 `upstream.base_url`（及必要时 `chat_path`）。`config.yaml` 内附有其它上游注释示例；也可参考 [`config.examples/`](config.examples/) 下的完整模板。

同步更新 `.env` 中的 `UPSTREAM_API_KEY` 为对应中转商的 Key。

### API Key（`.env`）

```bash
cp .env.example .env
# 填写 UPSTREAM_API_KEY
```

仍兼容旧变量名 `JIUTIAN_API_KEY`。

## 前置准备：安装并配置ngrok

**Windows**

```powershell
winget install ngrok.ngrok
ngrok config add-authtoken <token>
```

**macOS**

```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <token>
```

**Linux**

从 [ngrok 下载页](https://ngrok.com/download) 安装后执行 `ngrok config add-authtoken <token>`。

**macOS / Linux**：首次使用脚本前赋予执行权限：

```bash
chmod +x start.sh stop.sh tunnel.sh scripts/port.sh
```

## 项目启动步骤

需同时运行 **本地代理** + **ngrok**。Cursor Base URL 使用 ngrok 的 `https://...`（是否加 `/v1` 以实测为准）。

### 步骤 1：启动代理

**Windows**

```powershell
.\start.ps1
```

**macOS / Linux**

```bash
./start.sh
```

自测：`curl http://127.0.0.1:8787/health`

### 步骤 2：ngrok

**Windows**

```powershell
.\tunnel.ps1
```

**macOS / Linux**

```bash
./tunnel.sh
```

记下 `Forwarding https://xxxx.ngrok-free.app`。

### 步骤 3：Cursor

1. **OpenAI API Key**：可填 `local`
2. **Override OpenAI Base URL**：`https://xxxx.ngrok-free.app/v1`（或按你环境实测去掉 `/v1`）
3. **Add Custom Model**：名称与 `config.yaml` 中 `model_aliases` 的**左侧键**一致

### 停止

| 系统 | 停止代理 | 停止 ngrok |
|------|----------|------------|
| Windows | `.\stop.ps1` 或终端 A `Ctrl+C` | 终端 B `Ctrl+C` |
| macOS / Linux | `./stop.sh` 或 `Ctrl+C` | `Ctrl+C` |

## 项目脚本

| 作用 | Windows | macOS / Linux |
|------|---------|---------------|
| 启动代理 | `start.ps1` | `start.sh` |
| ngrok | `tunnel.ps1` | `tunnel.sh` |
| 停止代理 | `stop.ps1` | `stop.sh` |

## 排错

| 现象 | 处理 |
|------|------|
| `Access to private networks is forbidden` | 使用 ngrok HTTPS，勿填 `127.0.0.1` |
| `UPSTREAM_API_KEY is not set` | 检查 `.env` 并重启代理 |
| `Model name is not valid` | Cursor 用别名（左侧），勿用带 `/` 的上游 id |
| 改配置不生效 | 修改 `config.yaml` 后必须 `stop` 再 `start` |
| 404 | 检查 `base_url` + `chat_path` 拼接 |
| `start.sh` permission denied | `chmod +x *.sh scripts/*.sh` |

## 架构

```text
Cursor → ngrok (HTTPS) → 127.0.0.1:8787/v1/chat/completions
      → 本地代理（读 config.yaml）→ 上游 OpenAI 兼容 API
```
