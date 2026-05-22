# Cursor OpenAI Bridge

[中文文档](README.md)

A local OpenAI-compatible proxy built with **Python (FastAPI)** and **ngrok** tunneling, so **Cursor** can reliably use multiple **OpenAI-compatible API gateways** (OpenRouter, Jiutian MoMA, One API, and others).

It addresses three common blockers: Cursor rejecting model ids with `/`, upstream paths that differ from Cursor’s default `/v1/chat/completions`, and Cursor’s cloud backend being unable to reach `127.0.0.1`. The proxy provides **model alias mapping**, **path rewriting**, and a public HTTPS entry via ngrok.

All runtime settings are in [`config.yaml`](config.yaml) at the project root—edit this single file to switch providers or models.

## Problems it solves

| Cursor limitation | How the proxy handles it |
|-------------------|---------------------------|
| Rejects model names with `/` (e.g. `z.ai/glm-5.1`) | `model_aliases` mapping |
| Non-standard paths (not `/v1/chat/completions`) | Configurable `chat_path` |
| Cannot reach `127.0.0.1` (`private networks forbidden`) | Expose via **ngrok** as public HTTPS |

## When you need this proxy

| Situation | Recommendation |
|-----------|----------------|
| Gateway is already public HTTPS + standard `/v1`, and Cursor accepts model ids | **Connect Cursor directly**—no proxy needed |
| Model ids contain `/`, or path is `/v3`, etc. | **Use this proxy** |
| Upstream is only reachable on a private network | Proxy + ngrok |

## Requirements

- Python 3.10+
- [ngrok](https://ngrok.com/)
- Cursor Pro+ (custom OpenAI-compatible models)

## Configuration (edit `config.yaml` only)

### Switch models

Edit `model_aliases`: **left** = name in Cursor, **right** = real upstream model id.

```yaml
model_aliases:
  GLM-5.1: "z.ai/glm-5.1"
  # deepseek-v4-flash: "deepseek/deepseek-v4-flash"   # comment out to disable
  qwen3.5-27b: "qwen/qwen3.5-27b"
```

Add/select a custom model in Cursor using the **left-hand** name. After changes, run `stop` then `start` to restart the proxy.

### Switch upstream gateway

Edit `provider` and `upstream.base_url` (and `chat_path` if needed). See commented examples inside `config.yaml`, or full templates under [`config.examples/`](config.examples/).

Update `UPSTREAM_API_KEY` in `.env` to match the new provider.

### API key (`.env`)

```bash
cp .env.example .env
# Set UPSTREAM_API_KEY
```

The legacy env name `JIUTIAN_API_KEY` is still supported.

## One-time setup: ngrok

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

Install from the [ngrok download page](https://ngrok.com/download), then run `ngrok config add-authtoken <token>`.

**macOS / Linux** — make scripts executable once:

```bash
chmod +x start.sh stop.sh tunnel.sh scripts/port.sh
```

## Daily workflow

Run **local proxy** and **ngrok** together. In Cursor, set Base URL to ngrok’s `https://...` (whether to append `/v1` depends on your setup—test it).

### Step 1: Start the proxy

**Windows**

```powershell
.\start.ps1
```

**macOS / Linux**

```bash
./start.sh
```

Smoke test: `curl http://127.0.0.1:8787/health`

### Step 2: Start ngrok

**Windows**

```powershell
.\tunnel.ps1
```

**macOS / Linux**

```bash
./tunnel.sh
```

Note the line like: `Forwarding https://xxxx.ngrok-free.app -> http://127.0.0.1:8787`

### Step 3: Configure Cursor

1. **OpenAI API Key**: can be `local` (real key is injected from `.env` by the proxy)
2. **Override OpenAI Base URL**: `https://xxxx.ngrok-free.app/v1` (or without `/v1` if that works for you)
3. **Add Custom Model**: same as the **left-hand keys** in `config.yaml` `model_aliases`

### Stop

| OS | Stop proxy | Stop ngrok |
|----|------------|------------|
| Windows | `.\stop.ps1` or `Ctrl+C` in terminal A | `Ctrl+C` in terminal B |
| macOS / Linux | `./stop.sh` or `Ctrl+C` | `Ctrl+C` |

## Scripts

| Purpose | Windows | macOS / Linux |
|---------|---------|---------------|
| Start proxy | `start.ps1` | `start.sh` |
| ngrok tunnel | `tunnel.ps1` | `tunnel.sh` |
| Stop proxy | `stop.ps1` | `stop.sh` |

## Reference templates

The [`config.examples/`](config.examples/) directory contains sample configs (Jiutian, OpenRouter, One API, generic). **Do not overwrite** `config.yaml` with them—copy fields manually into `config.yaml` as needed.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Access to private networks is forbidden` | Use ngrok HTTPS URL; do not use `127.0.0.1` in Cursor |
| `UPSTREAM_API_KEY is not set` | Check `.env` and restart the proxy |
| `Model name is not valid` | Use alias (left side in yaml), not upstream id with `/` |
| Config changes ignored | After editing `config.yaml`, run `stop` then `start` |
| 404 | Verify `base_url` + `chat_path` combine to the correct endpoint |
| `start.sh: permission denied` | `chmod +x *.sh scripts/*.sh` |

## Architecture

```text
Cursor → ngrok (HTTPS) → 127.0.0.1:8787/v1/chat/completions
      → local proxy (reads config.yaml) → upstream OpenAI-compatible API
```
