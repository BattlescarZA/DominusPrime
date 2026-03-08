<div align="center">

# DominusPrime

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-black.svg?logo=github)](https://github.com/BattlescarZA/DominusPrime)
[![PyPI](https://img.shields.io/pypi/v/dominusprime?color=3775A9&label=PyPI&logo=pypi)](https://pypi.org/project/dominusprime/)
[![Python Version](https://img.shields.io/badge/python-3.10%20~%20%3C3.14-blue.svg?logo=python&label=Python)](https://www.python.org/downloads/)
[![Last Commit](https://img.shields.io/github/last-commit/BattlescarZA/DominusPrime)](https://github.com/BattlescarZA/DominusPrime)
[![License](https://img.shields.io/badge/license-Apache%202.0-red.svg?logo=apache&label=License)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black.svg?logo=python&label=CodeStyle)](https://github.com/psf/black)
[![GitHub Stars](https://img.shields.io/github/stars/BattlescarZA/DominusPrime?style=flat&logo=github&color=yellow&label=Stars)](https://github.com/BattlescarZA/DominusPrime/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/BattlescarZA/DominusPrime?style=flat&logo=github&color=purple&label=Forks)](https://github.com/BattlescarZA/DominusPrime/network)

[[中文 README](README_zh.md)] [[日本語](README_ja.md)]

<p align="center">
  <img src="https://img.alicdn.com/imgextra/i2/O1CN014TIqyO1U5wDiSbFfA_!!6000000002467-2-tps-816-192.png" alt="DominusPrime Logo" width="120">
</p>

<p align="center"><b>Works for you, grows with you.</b></p>

</div>

Your Personal AI Assistant; easy to install, deploy on your own machine or on the cloud; supports multiple chat apps with easily extensible capabilities.

> **Core capabilities:**
>
> **Every channel** — DingTalk, Feishu, QQ, Discord, iMessage, and more. One assistant, connect as you need.
>
> **Under your control** — Memory and personalization under your control. Deploy locally or in the cloud; scheduled reminders to any channel.
>
> **Skills** — Built-in cron; custom skills in your workspace, auto-loaded. No lock-in.
>
> <details>
> <summary><b>What you can do</b></summary>
>
> <br>
>
> - **Social**: daily digest of hot posts (Xiaohongshu, Zhihu, Reddit), Bilibili/YouTube summaries.
> - **Productivity**: newsletter digests to DingTalk/Feishu/QQ, contacts from email/calendar.
> - **Creative**: describe your goal, run overnight, get a draft next day.
> - **Research**: track tech/AI news, personal knowledge base.
> - **Desktop**: organize files, read/summarize docs, request files in chat.
> - **Explore**: combine Skills and cron into your own agentic app.
>
> </details>

---

## Table of Contents

> **Recommended reading:**
>
> - **I want to run DominusPrime in 3 commands**: [Quick Start](#quick-start) → open Console in browser.
> - **I want to chat in DingTalk / Feishu / QQ**: Configure [channels](https://DominusPrime.agentscope.io/docs/channels) in the Console.
> - **I don’t want to install Python**: [One-line install](#one-line-install-beta-continuously-improving) handles Python automatically, or use [ModelScope one-click](https://modelscope.cn/studios/fork?target=AgentScope/DominusPrime) for cloud deployment.

- [News](#news)
- [Quick Start](#quick-start)
- [API Key](#api-key)
- [Local Models](#local-models)
- [Documentation](#documentation)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#get-involved)
- [Install from source](#install-from-source)
- [Why DominusPrime?](#why-DominusPrime)
- [Built by](#built-by)
- [License](#license)

---

## Quick Start

### pip install (recommended)

If you prefer managing Python yourself:

```bash
pip install DominusPrime
DominusPrime init --defaults
DominusPrime app
```

Then open **http://127.0.0.1:9999/** in your browser for the Console (chat with DominusPrime, configure the agent). To talk in DingTalk, Feishu, QQ, etc., add a channel in the [docs](https://DominusPrime.agentscope.io/docs/channels).

![Console](https://img.alicdn.com/imgextra/i4/O1CN01z9VY6z1uMad7pgrCj_!!6000000006023-2-tps-3822-2064.png)

### One-line install (beta, continuously improving)

No Python required — the installer handles everything for you:

**macOS / Linux:**

```bash
curl -fsSL https://DominusPrime.agentscope.io/install.sh | bash
```

To install with Ollama support:

```bash
curl -fsSL https://DominusPrime.agentscope.io/install.sh | bash -s -- --extras ollama
```

To install with multiple extras (e.g., Ollama + llama.cpp):

```bash
curl -fsSL https://DominusPrime.agentscope.io/install.sh | bash -s -- --extras ollama,llamacpp
```

**Windows (CMD):**

```CMD
curl -fsSL https://DominusPrime.agentscope.io/install.bat -o install.bat && install.bat
```

**Windows (PowerShell):**

```powershell
irm https://DominusPrime.agentscope.io/install.ps1 | iex
```

> **Note**: The installer will automatically check the status of uv. If it is not installed, it will attempt to download and configure it automatically. If the automatic installation fails, please follow the on-screen prompts or execute `python -m pip install -U uv`, then rerun the installer.

> **⚠️ Special Notice for Windows Enterprise LTSC Users**
>
> If you are using Windows LTSC or an enterprise environment governed by strict security policies, PowerShell may run in **Constrained Language Mode**, potentially causing the following issue:
> 1. **If using CMD (.bat): Script executes successfully but fails to write to `Path`**
>
>    The script completes file installation. Due to **Constrained Language Mode**, it cannot automatically update environment variables. Manually configure as follows:
>    - **Locate the installation directory**:
>      - Check if `uv` is available: Enter `uv --version` in CMD. If a version number appears, **only configure the DominusPrime path**. If you receive the prompt `'uv' is not recognized as an internal or external command, operable program or batch file,` configure both paths.
>      - uv path (choose one based on installation location; use if `uv` fails): Typically `%USERPROFILE%\.local\bin`, `%USERPROFILE%\AppData\Local\uv`, or the `Scripts` folder within your Python installation directory
>      - DominusPrime path: Typically located at `%USERPROFILE%\.DominusPrime\bin`.
>    - **Manually add to the system's Path environment variable**:
>      - Press `Win + R`, type `sysdm.cpl` and press Enter to open System Properties.
>      - Click “Advanced” -> “Environment Variables”.
>      - Under “System variables”, locate and select `Path`, then click “Edit”.
>      - Click “New”, enter both directory paths sequentially, then click OK to save.
> 2. **If using PowerShell (.ps1): Script execution interrupted**
>
>   Due to **Constrained Language Mode**, the script may fail to automatically download `uv`.
>   - **Manually install uv**: Refer to the [GitHub Release](https://github.com/astral-sh/uv/releases) to download `uv.exe` and place it in `%USERPROFILE%\.local\bin` or `%USERPROFILE%\AppData\Local\uv`; or ensure Python is installed and run `python -m pip install -U uv`.
>   - **Configure `uv` environment variables**: Add the `uv` directory and `%USERPROFILE%\.DominusPrime\bin` to your system's `Path` variable.
>   - **Re-run the installation**: Open a new terminal and execute the installation script again to complete the `DominusPrime` installation.
>   - **Configure the `DominusPrime` environment variable**: Add `%USERPROFILE%\.DominusPrime\bin` to your system's `Path` variable.

Once installed, open a new terminal and run:

```bash
DominusPrime init --defaults   # or: DominusPrime init (interactive)
DominusPrime app
```

<details>
<summary><b>Install options</b></summary>

**macOS / Linux:**

```bash
# Install a specific version
curl -fsSL ... | bash -s -- --version 0.0.2

# Install from source (dev/testing)
curl -fsSL ... | bash -s -- --from-source

# With local model support
bash install.sh --extras llamacpp    # llama.cpp (cross-platform)
bash install.sh --extras mlx         # MLX (Apple Silicon)
bash install.sh --extras llamacpp,mlx

# Upgrade — just re-run the installer
curl -fsSL ... | bash

# Uninstall
DominusPrime uninstall          # keeps config and data
DominusPrime uninstall --purge  # removes everything
```

**Windows (PowerShell):**

```powershell
# Install a specific version
irm ... | iex; .\install.ps1 -Version 0.0.2

# Install from source (dev/testing)
.\install.ps1 -FromSource

# With local model support
.\install.ps1 -Extras llamacpp      # llama.cpp (cross-platform)
.\install.ps1 -Extras mlx           # MLX
.\install.ps1 -Extras llamacpp,mlx

# Upgrade — just re-run the installer
irm ... | iex

# Uninstall
DominusPrime uninstall          # keeps config and data
DominusPrime uninstall --purge  # removes everything
```

</details>

### Using Docker

Images are on **Docker Hub** (`agentscope/DominusPrime`). Image tags: `latest` (stable); `pre` (PyPI pre-release).

```bash
docker pull agentscope/DominusPrime:latest
docker run -p 127.0.0.1:9999:9999 -v DominusPrime-data:/app/working agentscope/DominusPrime:latest
```

Also available on Alibaba Cloud Container Registry (ACR) for users in China: `agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/DominusPrime` (same tags).

Then open **http://127.0.0.1:9999/** for the Console. Config, memory, and skills are stored in the `DominusPrime-data` volume. To pass API keys (e.g. `DASHSCOPE_API_KEY`), add `-e VAR=value` or `--env-file .env` to `docker run`.

> **Connecting to Ollama or other services on the host machine**
>
> Inside a Docker container, `localhost` refers to the container itself, not your host machine. If you run Ollama (or other model services) on the host and want DominusPrime in Docker to reach them, use one of these approaches:
>
> **Option A** — Explicit host binding (all platforms):
> ```bash
> docker run -p 127.0.0.1:9999:9999 \
>   --add-host=host.docker.internal:host-gateway \
>   -v DominusPrime-data:/app/working agentscope/DominusPrime:latest
> ```
> Then in DominusPrime **Settings → Models → Ollama**, change the Base URL to `http://host.docker.internal:11434/v1` or your corresponding port.
>
> **Option B** — Host networking (Linux only):
> ```bash
> docker run --network=host -v DominusPrime-data:/app/working agentscope/DominusPrime:latest
> ```
> No port mapping (`-p`) is needed; the container shares the host network directly. Note that all container ports are exposed on the host, which may cause conflicts if the port is already in use.

The image is built from scratch. To build the image yourself, please refer to the [Build Docker image](scripts/README.md#build-docker-image) section in `scripts/README.md`, and then push to your registry.

### Using ModelScope

**No local install?** [ModelScope Studio](https://modelscope.cn/studios/fork?target=AgentScope/DominusPrime) one-click cloud setup. Set your Studio to **non-public** so others cannot control your DominusPrime.

### Deploy on Alibaba Cloud ECS

To run DominusPrime on Alibaba Cloud (ECS), use the one-click deployment: open the [DominusPrime on Alibaba Cloud (ECS) deployment link](https://computenest.console.aliyun.com/service/instance/create/cn-hangzhou?type=user&ServiceId=service-1ed84201799f40879884) and follow the prompts. For step-by-step instructions, see [Alibaba Cloud Developer: Deploy your AI assistant in 3 minutes](https://developer.aliyun.com/article/1713682).

---

## API Key

If you use a **cloud LLM** (e.g. DashScope, ModelScope), you must configure an API key before chatting. DominusPrime will not work until a valid key is set. See the [official docs](https://DominusPrime.agentscope.io/docs/models#configure-cloud-providers) for details.

**How to configure:**

1. **Console (recommended)** — After running `DominusPrime app`, open **http://127.0.0.1:9999/** → **Settings** → **Models**. Choose a provider, enter the **API Key**, and enable that provider and model.
2. **`DominusPrime init`** — When you run `DominusPrime init`, it will guide you through configuring the LLM provider and API key. Follow the prompts to choose a provider and enter your key.
3. **Environment variable** — For DashScope you can set `DASHSCOPE_API_KEY` in your shell or in a `.env` file in the working directory.

Tools that need extra keys (e.g. `TAVILY_API_KEY` for web search) can be set in Console **Settings → Environment variables**, or see [Config](https://DominusPrime.agentscope.io/docs/config) for details.

> **Using local models only?** If you use [Local Models](#local-models) (llama.cpp or MLX), you do **not** need any API key.

## Local Models

DominusPrime can run LLMs entirely on your machine — no API keys or cloud services required. See the [official docs](https://DominusPrime.agentscope.io/docs/models#local-providers-llamacpp--mlx) for details.

| Backend       | Best for                                 | Install                                                              |
| ------------- | ---------------------------------------- | -------------------------------------------------------------------- |
| **llama.cpp** | Cross-platform (macOS / Linux / Windows) | `pip install 'DominusPrime[llamacpp]'` or `bash install.sh --extras llamacpp` |
| **MLX**       | Apple Silicon Macs (M1/M2/M3/M4)         | `pip install 'DominusPrime[mlx]'` or `bash install.sh --extras mlx`         |
| **Ollama**    | Cross-platform (requires Ollama service) | `pip install 'DominusPrime[ollama]'` or `bash install.sh --extras ollama`   |

After installing, you can download and manage local models in the **Console** UI. You can also use the command line:

```bash
DominusPrime models download Qwen/Qwen3-4B-GGUF
DominusPrime models # select the downloaded model
DominusPrime app # start the server
```

---

## Documentation

| Topic                                                                 | Description                                      |
| --------------------------------------------------------------------- | ------------------------------------------------ |
| [Introduction](https://DominusPrime.agentscope.io/docs/intro)                | What DominusPrime is and how to use it                  |
| [Quick start](https://DominusPrime.agentscope.io/docs/quickstart)            | Install and run (local or ModelScope Studio)    |
| [Console](https://DominusPrime.agentscope.io/docs/console)                   | Web UI: chat and agent configuration            |
| [Models](https://DominusPrime.agentscope.io/docs/models)                     | Configure cloud, local, and custom providers    |
| [Channels](https://DominusPrime.agentscope.io/docs/channels)                  | DingTalk, Feishu, QQ, Discord, iMessage, and more |
| [Skills](https://DominusPrime.agentscope.io/docs/skills)                      | Extend and customize capabilities               |
| [MCP](https://DominusPrime.agentscope.io/docs/skills)                        | Manage MCP clients                               |
| [Memory](https://DominusPrime.agentscope.io/docs/memory)                     | Context and long-term memory                     |
| [Magic commands](https://DominusPrime.agentscope.io/docs/commands)           | Control conversation state without waiting for the AI |
| [Heartbeat](https://DominusPrime.agentscope.io/docs/heartbeat)                | Scheduled check-in and digest                    |
| [Config & working dir](https://DominusPrime.agentscope.io/docs/config) | Working directory and config file                |
| [CLI](https://DominusPrime.agentscope.io/docs/cli)                            | Init, cron jobs, skills, clean                   |
| [FAQ](https://DominusPrime.agentscope.io/docs/faq)                           | Common questions and troubleshooting             |

Full docs in this repo: [website/public/docs/](website/public/docs/).

---

## FAQ

For common questions, troubleshooting tips, and known issues, please visit the **[FAQ page](https://DominusPrime.agentscope.io/docs/faq)**.

---

## Roadmap

| Area | Item | Status |
| --- | --- | --- |
| Horizontal Expansion | More channels, models, skills, MCPs — **community contributions welcome** | Seeking Contributors |
| Existing Feature Extension | Display optimization, download hints, Windows path compatibility, etc. — **community contributions welcome** | Seeking Contributors |
| Console Web UI | Expose more info/config in the Console | In Progress |
| Compatibility & Ease of Use | App-level packaging (.dmg, .exe) | In Progress |
| Self-healing | Magic commands and daemon capabilities (CLI, status, restart, logs) | In Progress |
| | DaemonAgent: autonomous diagnostics, self-healing, and recovery | Planned |
| Multi-agent | Background task support | In Progress |
| | Multi-agent isolation | Planned |
| | Inter-agent contention resolution | Planned |
| | Multi-agent communication | Planned |
| Multimodal | Voice/video calls and real-time interaction | In Progress |
| Release & Contributing | Contributing guidance for vibe coding agents | Planned |
| Bugfixes & Enhancements | Skills and MCP runtime install, hot-reload improvements | Planned |
| Security | Shell execution confirmation | Planned |
| | Tool/skills security | Planned |
| | Configurable security levels (user-configurable) | Planned |
| Sandbox | Deeper integration with AgentScope Runtime sandboxes | Long-term Planning |
| DominusPrime-optimized local models | LLMs tuned for DominusPrime's native skills and common tasks; better local personal-assistant usability | Long-term Planning |
| Small + large model collaboration | Local LLMs for sensitive data; cloud LLMs for planning and coding; balance of privacy, performance, and capability | Long-term Planning |
| Cloud-native | Deeper integration with AgentScope Runtime; leverage cloud compute, storage, and tooling | Long-term Planning |
| Skills Hub | Enrich the [AgentScope Skills](https://github.com/agentscope-ai/agentscope-skills) repository and improve discoverability of high-quality skills | Long-term Planning |

*Status:* *In Progress* — actively being worked on; *Planned* — queued or under design, also **welcome contributions**; *Seeking Contributors* — we **strongly encourage community contributions**; *Long-term Planning* — longer-horizon roadmap.

### Get involved

We are building DominusPrime in the open and welcome contributions of all kinds! Check the [Roadmap](#roadmap) above (especially items marked **Seeking Contributors**) to find areas that interest you, and read [CONTRIBUTING](https://github.com/agentscope-ai/DominusPrime/blob/main/CONTRIBUTING.md) to get started. We particularly welcome:

- **Horizontal expansion** — new channels, model providers, skills, MCPs.
- **Existing feature extension** — display and UX improvements, download hints, Windows path compatibility, and the like.

Join the conversation on [GitHub Discussions](https://github.com/agentscope-ai/DominusPrime/discussions) to suggest or pick up work.

---

## Install from source

```bash
git clone https://github.com/agentscope-ai/DominusPrime.git
cd DominusPrime

# Build console frontend first (required for web UI)
cd console && npm ci && npm run build
cd ..

# Copy console build output to package directory
mkdir -p src/DominusPrime/console
cp -R console/dist/. src/DominusPrime/console/

# Install Python package
pip install -e .
```

- **Dev** (tests, formatting): `pip install -e ".[dev]"`
- **Then**: Run `DominusPrime init --defaults`, then `DominusPrime app`.

---

## Why DominusPrime?

DominusPrime represents both a **Co Personal Agent Workstation** and a "co-paw"—a partner always by your side. More than just a cold tool, DominusPrime is a warm "little paw" always ready to lend a hand (or a paw!). It is the ultimate teammate for your digital life.

---

## Built by

[AgentScope team](https://github.com/agentscope-ai) · [AgentScope](https://github.com/agentscope-ai/agentscope) · [AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime) · [ReMe](https://github.com/agentscope-ai/ReMe)

---

## Contact us

| [Discord](https://discord.gg/eYMpfnkG8h)                     | [X (Twitter)](https://x.com/agentscope_ai)                   | [DingTalk](https://qr.dingtalk.com/action/joingroup?code=v1,k1,OmDlBXpjW+I2vWjKDsjvI9dhcXjGZi3bQiojOq3dlDw=&_dt_no_comment=1&origin=11) |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| [<img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="80" height="80" alt="Discord">](https://discord.gg/eYMpfnkG8h) | [<img src="https://img.shields.io/badge/X-black.svg?logo=x&logoColor=white" width="80" height="80" alt="X">](https://x.com/agentscope_ai) | [<img src="https://img.alicdn.com/imgextra/i2/O1CN01vCWI8a1skHtLGXEMQ_!!6000000005804-2-tps-458-460.png" width="80" height="80" alt="DingTalk">](https://qr.dingtalk.com/action/joingroup?code=v1,k1,OmDlBXpjW+I2vWjKDsjvI9dhcXjGZi3bQiojOq3dlDw=&_dt_no_comment=1&origin=11) |

---

## License

DominusPrime is released under the [Apache License 2.0](LICENSE).

---

## Contributors

All thanks to our contributors:

<a href="https://github.com/agentscope-ai/DominusPrime/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agentscope-ai/DominusPrime" alt="Contributors" />
</a>
