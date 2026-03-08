# DominusPrime FAQ

Welcome to the DominusPrime Frequently Asked Questions! This comprehensive guide covers installation, configuration, features, troubleshooting, and more.

---

## 📦 Installation & Setup

### How do I install DominusPrime?

DominusPrime supports multiple installation methods:

**1. One-line installer (Recommended)**
```bash
# macOS / Linux:
curl -fsSL https://raw.githubusercontent.com/BattlescarZA/DominusPrime/main/scripts/install.sh | bash

# Windows (PowerShell):
irm https://raw.githubusercontent.com/BattlescarZA/DominusPrime/main/scripts/install.ps1 | iex

# Windows (CMD):
# Download and run install.bat from the repository
```

**2. Install with pip**

Requirements: Python >= 3.10, < 3.14

```bash
pip install dominusprime
```

**3. Install from source**
```bash
git clone https://github.com/BattlescarZA/DominusPrime.git
cd DominusPrime
pip install -e .
```

**4. Docker installation**
```bash
docker pull battlescarz/dominusprime:latest
docker run -p 127.0.0.1:8088:8088 -v dominusprime-data:/app/working battlescarz/dominusprime:latest
```

Then open `http://127.0.0.1:8088/` in your browser.

### What are the system requirements?

- **Python**: 3.10 to 3.13 (< 3.14)
- **Operating Systems**: Windows 10/11, macOS, Linux
- **RAM**: Minimum 4GB (8GB+ recommended for local models)
- **Storage**: 2GB+ for application and dependencies

### How do I update DominusPrime?

**If installed via pip:**
```bash
pip install --upgrade dominusprime
```

**If installed from source:**
```bash
cd DominusPrime
git pull origin 0.9.2
pip install -e .
```

**If using Docker:**
```bash
docker pull battlescarz/dominusprime:latest
docker stop dominusprime  # Stop current container
docker run -p 127.0.0.1:8088:8088 -v dominusprime-data:/app/working battlescarz/dominusprime:latest
```

After upgrading, restart the service with `dominusprime app`.

---

## 🚀 Getting Started

### How do I start DominusPrime?

After installation, run:
```bash
dominusprime app
```

The console UI will be available at `http://127.0.0.1:8088/`

### How do I configure my first AI model?

1. Start DominusPrime with `dominusprime app`
2. Open the console at `http://127.0.0.1:8088/`
3. Navigate to "Models" in the sidebar
4. Click "Add Model" and select your provider:
   - OpenAI
   - Azure OpenAI
   - Anthropic
   - Local models (Ollama, llama.cpp, MLX)
   - Other OpenAI-compatible providers
5. Enter your API key and configuration
6. Click "Test" to verify connection
7. Save the configuration

### What channels (communication platforms) are supported?

DominusPrime supports multiple communication channels:

- **DingTalk** - Chinese enterprise communication
- **Feishu (Lark)** - International enterprise platform
- **QQ** - Popular Chinese messaging app
- **Discord** - Gaming and community platform
- **iMessage** - Apple's messaging service (macOS only)
- **Telegram** - Privacy-focused messaging
- **Twilio Voice** - Voice call integration
- **Console** - Built-in web interface

### How do I set up a channel?

1. Navigate to "Channels" in the console
2. Click "Add Channel"
3. Select the channel type
4. Follow the platform-specific setup:
   - For DingTalk/Feishu: Create bot and get webhook URL
   - For Discord: Create bot and get token
   - For Telegram: Use BotFather to create bot and get token
   - For iMessage: macOS only, no additional setup needed
5. Configure channel settings (prefix, filters, etc.)
6. Save and test the channel

---

## 🎯 Features & Capabilities

### What can DominusPrime do?

**Core Capabilities:**
- **Multi-channel AI Assistant**: Connect to DingTalk, Feishu, QQ, Discord, iMessage, Telegram
- **Custom Skills**: Create and use custom skills with automatic loading
- **Scheduled Tasks**: Built-in cron for automated reminders and tasks
- **Memory Management**: Personalized memory with context awareness
- **MCP Integration**: Model Context Protocol for extended capabilities
- **Local & Cloud Deployment**: Run locally or deploy to cloud
- **Multiple AI Models**: Support for OpenAI, Anthropic, local models (Ollama, llama.cpp, MLX)

**Use Cases:**
- Social: Daily digests from Reddit, YouTube summaries
- Productivity: Newsletter digests to channels, calendar integration
- Creative: Overnight content generation
- Research: Tech news tracking, knowledge base management
- Desktop: File organization, document summarization
- Custom: Build your own agentic applications with Skills and cron

### What are Skills?

Skills are custom capabilities you can add to DominusPrime. They're Python functions that extend the agent's abilities:

- **Built-in Skills**: Search, file operations, web browsing
- **Custom Skills**: Create your own in `~/.dominusprime/skills/`
- **Auto-loading**: Skills are automatically discovered and loaded
- **No lock-in**: Skills are standard Python code

To create a skill, place a Python file in `~/.dominusprime/skills/` following the skill template.

### How does memory work?

DominusPrime includes intelligent memory management:

- **Conversation Memory**: Remembers context within conversations
- **Long-term Memory**: Stores important information across sessions
- **Memory Compaction**: Automatically summarizes old conversations to save tokens
- **Embedding Support**: Uses embeddings for semantic search in memory
- **Configurable**: Adjust memory size, compaction ratio, and retention

### What is MCP (Model Context Protocol)?

MCP allows DominusPrime to connect to external tools and services:

- File system access
- Database connections
- API integrations
- Custom tool implementations

Configure MCP clients in the console under "MCP" settings.

---

## 🔧 Configuration & Customization

### Where are configuration files stored?

**Default locations:**
- **Working Directory**: `~/.dominusprime/`
- **Configuration**: `~/.dominusprime/config.json`
- **Secrets**: `~/.dominusprime.secret/` (providers.json, envs.json)
- **Skills**: `~/.dominusprime/skills/`
- **Logs**: `~/.dominusprime/logs/`

You can change the working directory with:
```bash
dominusprime app --dir /custom/path
```

### How do I configure environment variables?

Use the built-in environment manager:
```bash
# Set environment variable
dominusprime env set OPENAI_API_KEY "sk-..."

# List all variables
dominusprime env list

# Remove variable
dominusprime env remove OPENAI_API_KEY
```

Or edit `~/.dominusprime.secret/envs.json` directly.

### How do I customize the agent's behavior?

1. **System Prompt**: Configure in the console under Chat settings
2. **Model Parameters**: Adjust temperature, top_p, max_tokens in model config
3. **Channel Filters**: Enable/disable tool messages and thinking content per channel
4. **Memory Settings**: Configure compaction ratio and context size
5. **Skills**: Add custom skills for new capabilities

### Can I run multiple instances?

Yes! Use different working directories:

```bash
# Instance 1
dominusprime app --dir ~/.dominusprime-work

# Instance 2 (different port)
dominusprime app --dir ~/.dominusprime-personal --port 8089
```

---

## 🔌 Model Configuration

### What AI models are supported?

**Cloud Providers:**
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Azure OpenAI
- Anthropic (Claude 3.5, Claude 3)
- DeepSeek
- Any OpenAI-compatible API

**Local Models:**
- Ollama (easiest for local deployment)
- llama.cpp (for raw model files)
- MLX (optimized for Apple Silicon)

### How do I use Ollama with DominusPrime?

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Pull a model**: `ollama pull llama2`
3. **In DominusPrime console**:
   - Go to "Models" → "Add Model"
   - Select "Ollama"
   - Base URL: `http://localhost:11434` (default)
   - Model: Select from available models
   - Test and save

### How do I connect Ollama in Docker to host machine?

**Method 1: Use host network (Linux only)**
```bash
docker run --network host -v dominusprime-data:/app/working battlescarz/dominusprime:latest
```

**Method 2: Use host.docker.internal (Windows/Mac)**
In model configuration, use:
- Base URL: `http://host.docker.internal:11434`

**Method 3: Bridge network with host IP**
Find your host IP and use:
- Base URL: `http://YOUR_HOST_IP:11434`

### Can I use multiple models at once?

Yes! Configure multiple model providers:
1. Add models in the console
2. Set different models for different purposes
3. Switch models per conversation or channel

---

## 🛠️ Troubleshooting

### DominusPrime won't start

**Check these common issues:**

1. **Port already in use**:
   ```bash
   # Use a different port
   dominusprime app --port 8089
   ```

2. **Python version**:
   ```bash
   python --version  # Should be 3.10 - 3.13
   ```

3. **Missing dependencies**:
   ```bash
   pip install --upgrade dominusprime
   ```

4. **Check logs**:
   ```bash
   # Logs are in ~/.dominusprime/logs/
   tail -f ~/.dominusprime/logs/app.log
   ```

### Model connection fails

1. **Verify API key**: Check that your API key is correct
2. **Test network**: Ensure you can reach the API endpoint
3. **Check quotas**: Verify you haven't exceeded API limits
4. **Review logs**: Check console logs for detailed error messages

### Channel not receiving messages

1. **Verify webhook URL**: Ensure the webhook is correctly configured
2. **Check permissions**: Bot needs proper permissions in the platform
3. **Test manually**: Try sending a test message
4. **Review channel logs**: Check logs for connection errors

### Memory/Performance issues

1. **Reduce context size**: Lower `max_tokens` in model config
2. **Enable compaction**: Turn on automatic memory compaction
3. **Limit skills**: Disable unused skills
4. **Check system resources**: Monitor RAM and CPU usage

### "Module not found" errors

```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall dominusprime
```

### Windows-specific issues

**Constrained Language Mode (Enterprise/LTSC)**:
- If using `.bat`: Script runs but doesn't update PATH → Manually add `%USERPROFILE%\.dominusprime\bin` to PATH
- If using `.ps1`: Script fails → Manually install `uv` and add to PATH, then re-run script

**PowerShell Execution Policy**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📱 Mobile & UI

### Is there a mobile app?

The console UI is mobile-responsive! Access `http://YOUR_IP:8088/` from your mobile browser.

Features:
- Touch-friendly interface
- Collapsible sidebar with hamburger menu
- Responsive chat layout
- 44px minimum tap targets
- Optimized for phones and tablets

### Can I access the console remotely?

**For local network access:**
```bash
dominusprime app --host 0.0.0.0
```
Then access from `http://YOUR_LOCAL_IP:8088/`

**⚠️ Security Warning**: Only expose to trusted networks. For internet access, use:
- VPN connection
- Reverse proxy with authentication (nginx, Caddy)
- SSH tunnel

### Can I customize the UI?

The console UI is built with React and can be customized:
1. Clone the repository
2. Modify files in `console/src/`
3. Build with `npm run build` in the `console/` directory
4. Copy `console/dist/*` to `src/dominusprime/console/`

---

## 🔐 Security & Privacy

### Where is my data stored?

All data is stored locally in `~/.dominusprime/` and `~/.dominusprime.secret/`:
- Conversation history
- Model configurations
- API keys (in encrypted storage)
- Skills and custom code

**Privacy**: DominusPrime doesn't send your data anywhere except to the AI model APIs you configure.

### How are API keys stored?

API keys are stored in `~/.dominusprime.secret/` with restricted permissions (0600).

**Docker users**: Use volume mounts to persist secrets:
```bash
-v $HOME/.dominusprime.secret:/app/.dominusprime.secret
```

### Can I use DominusPrime offline?

Yes, with local models:
1. Install Ollama or llama.cpp
2. Download models locally
3. Configure DominusPrime to use local models
4. No internet connection required for inference

Note: Initial setup and updates require internet.

---

## 🤝 Advanced Topics

### How do I run DominusPrime as a service?

**Using systemd (Linux)**:
```bash
dominusprime daemon start  # Start as background service
dominusprime daemon status # Check status
dominusprime daemon restart # Restart service
dominusprime daemon stop   # Stop service
```

**Windows**: Use Task Scheduler or NSSM to create a Windows service

### How do I deploy to the cloud?

**Docker deployment** (recommended):
1. Build or pull Docker image
2. Deploy to your cloud provider (AWS, GCP, Azure, etc.)
3. Configure persistent volumes for data
4. Set up reverse proxy (nginx, Caddy) with SSL
5. Configure firewall rules

**Direct deployment**:
1. Install Python and dependencies on server
2. Clone repository or install via pip
3. Configure systemd service
4. Set up nginx reverse proxy with SSL
5. Configure firewall

### Can I contribute to DominusPrime?

Yes! DominusPrime is open source:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run pre-commit checks
5. Submit a pull request

See [CONTRIBUTING.md](https://github.com/BattlescarZA/DominusPrime/blob/main/CONTRIBUTING.md) for guidelines.

### How do I create custom skills?

1. Create a Python file in `~/.dominusprime/skills/`
2. Define functions with proper decorators
3. DominusPrime auto-loads skills on startup

**Example skill structure:**
```python
from dominusprime.agents.skills import skill

@skill
def my_custom_skill(parameter: str) -> str:
    """
    Description of what this skill does.
    
    Args:
        parameter: Description of the parameter
        
    Returns:
        Result description
    """
    # Your implementation here
    return f"Processed: {parameter}"
```

### What's the difference between DominusPrime and CoPaw?

DominusPrime is a specialized fork/variant focused on:
- Business-oriented features
- Enhanced UI/UX
- Custom branding and configurations
- Optimized for specific use cases

Both share the same core architecture and most features are compatible.

---

## 📚 Resources

### Where can I find documentation?

- **GitHub Repository**: https://github.com/BattlescarZA/DominusPrime
- **README**: Comprehensive getting started guide
- **Console Help**: Built-in documentation in the web UI
- **Community**: GitHub Issues and Discussions

### How do I report bugs?

1. Check existing issues: https://github.com/BattlescarZA/DominusPrime/issues
2. If new, create an issue with:
   - DominusPrime version (`dominusprime --version`)
   - Operating system and Python version
   - Steps to reproduce
   - Error messages and logs
   - Expected vs actual behavior

### Where can I get help?

- **GitHub Issues**: For bug reports
- **GitHub Discussions**: For questions and ideas
- **GitHub Wiki**: This FAQ and guides

### What's the project's license?

DominusPrime is licensed under Apache License 2.0, which allows:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

See [LICENSE](https://github.com/BattlescarZA/DominusPrime/blob/main/LICENSE) for full details.

---

## 🎉 Tips & Best Practices

### Performance optimization tips

1. **Use appropriate model sizes**: Smaller models for simple tasks
2. **Enable memory compaction**: Reduces token usage
3. **Limit context window**: Set reasonable `max_tokens`
4. **Use local models for repetitive tasks**: Saves API costs
5. **Batch operations**: Use skills for bulk operations

### Cost optimization for cloud models

1. **Use cheaper models for simple tasks**: GPT-3.5 vs GPT-4
2. **Enable message filtering**: Hide tool messages when not needed
3. **Adjust temperature**: Lower values = more deterministic = fewer retries
4. **Set token limits**: Prevent runaway generations
5. **Monitor usage**: Check API usage regularly

### Best practices for skills

1. **Keep skills focused**: One skill, one purpose
2. **Document thoroughly**: Clear docstrings
3. **Handle errors gracefully**: Return helpful error messages
4. **Test locally**: Verify before deploying
5. **Version control**: Keep skills in git

### Security best practices

1. **Never commit API keys**: Use environment variables
2. **Restrict network access**: Bind to localhost when possible
3. **Use HTTPS in production**: Always use SSL/TLS
4. **Regular updates**: Keep DominusPrime and dependencies updated
5. **Audit skills**: Review custom skills for security issues

---

## 🔄 Version History

### How do I check my version?

```bash
dominusprime --version
```

### Where can I see release notes?

Check the [Releases page](https://github.com/BattlescarZA/DominusPrime/releases) on GitHub.

### What's new in v0.9.2?

Current branch focuses on:
- Enhanced mobile responsiveness
- Updated branding and UI
- Improved URL references
- Bug fixes and stability improvements

---

**Last Updated**: March 2026  
**Current Version**: 0.9.2

For more questions, visit our [GitHub Discussions](https://github.com/BattlescarZA/DominusPrime/discussions)!
