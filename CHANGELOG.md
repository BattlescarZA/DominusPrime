# Changelog

All notable changes to this project will be documented in this file.

## [0.9.12] - 2026-03-31

### Added
- **WhatsApp Baileys Integration (Phase 1)**: Complete rewrite of WhatsApp integration using modern Baileys library
  - Node.js HTTP bridge ([`bridge.js`](scripts/whatsapp-bridge/bridge.js)) with REST API endpoints
  - Python adapter ([`baileys_adapter.py`](src/dominusprime/app/channels/whatsapp/baileys_adapter.py)) with subprocess management
  - Native message editing support (Baileys-exclusive feature)
  - Superior media handling (images, videos, audio, documents)
  - User allowlist security with LID ↔ phone mapping
  - Self-chat and bot modes
  - Auto npm dependency installation
- **WhatsApp CLI Commands**: New [`dominusprime whatsapp`](src/dominusprime/cli/whatsapp_cmd.py) command group
  - `dominusprime whatsapp pair` - QR code pairing
  - `dominusprime whatsapp status` - Check bridge status
  - `dominusprime whatsapp start` - Manual bridge start
  - `dominusprime whatsapp reset` - Reset session
- **Documentation**: Comprehensive guides
  - [`scripts/whatsapp-bridge/README.md`](scripts/whatsapp-bridge/README.md) - Bridge documentation (200+ lines)
  - [`docs/WHATSAPP_BAILEYS_IMPLEMENTATION.md`](docs/WHATSAPP_BAILEYS_IMPLEMENTATION.md) - Implementation guide (500+ lines)
  - [`plans/hermes-agent-feature-analysis.md`](plans/hermes-agent-feature-analysis.md) - Feature analysis and roadmap (600+ lines)

### Changed
- Bumped version from 0.9.11 to 0.9.12
- WhatsApp module now exports both [`WhatsAppChannel`](src/dominusprime/app/channels/whatsapp/channel.py) (old) and [`WhatsAppBaileysAdapter`](src/dominusprime/app/channels/whatsapp/baileys_adapter.py) (new)

### Technical Details
- **Bridge Architecture**: HTTP/JSON communication over localhost:3000
- **Session Management**: Multi-file auth state for reliability
- **Dependencies**: @whiskeysockets/baileys 7.0.0-rc.9, @hapi/boom, express, pino, qrcode-terminal
- **Security**: Session lock mechanism, user allowlist, automatic echo filtering
- **Testing**: 15+ unit tests for adapter and allowlist functionality

### Migration Path
- Existing whatsapp-web.js users can continue using `WhatsAppChannel`
- New users should use `WhatsAppBaileysAdapter` for better reliability
- See [`docs/WHATSAPP_BAILEYS_IMPLEMENTATION.md`](docs/WHATSAPP_BAILEYS_IMPLEMENTATION.md) for migration guide

### Comparison: Baileys vs whatsapp-web.js
| Feature | Baileys (0.9.12) | whatsapp-web.js (0.9.9) |
|---------|------------------|-------------------------|
| Maintenance Status | ✅ Active | ❌ Deprecated |
| Message Editing | ✅ Native | ❌ Not supported |
| Media Handling | ✅ Native binary | ⚠️ Base64 conversion |
| Session Format | ✅ Multi-file | ⚠️ Single file |
| Connection Stability | ✅ Excellent | ⚠️ Frequent drops |

## [0.9.9] - 2026-03-21

### Added

- **WhatsApp Web Integration**: Full WhatsApp Web functionality with QR code authentication
  - Node.js bridge service ([`bridge.js`](src/dominusprime/app/channels/whatsapp/bridge.js)) using whatsapp-web.js
  - Real-time WebSocket communication between Python and Node.js
  - QR code display in React frontend ([`WhatsAppQRDisplay.tsx`](console/src/pages/Control/Channels/components/WhatsAppQRDisplay.tsx))
  - Session persistence for WhatsApp authentication
  - Support for individual and group chats
  - Media handling (images, videos, audio, documents)
  - Typing indicators and read receipts
  - Connection status monitoring
  - Comprehensive setup documentation ([`README.md`](src/dominusprime/app/channels/whatsapp/README.md))

### Changed

- Updated [`WhatsAppConfig`](src/dominusprime/config/config.py) with bridge_url configuration
- Removed Bot Prefix field from WhatsApp channel settings (not applicable for WhatsApp Web)
- Enhanced [`WhatsAppChannel`](src/dominusprime/app/channels/whatsapp/channel.py) with async bridge communication

### Technical Details

- **Architecture**: Phone → WhatsApp Web (Puppeteer) → Node.js Bridge (port 8765) → Python Channel → Agent
- **Dependencies**: whatsapp-web.js ^1.23.0, express ^4.18.2, socket.io ^4.6.1
- **Frontend**: Added qrcode.react ^4.1.0, socket.io-client ^4.8.1

## [0.9.8] - 2026-03-20

### Added

- **Experience Distillation & Skill Extraction**: Automatically learn from conversations and generate reusable markdown skills
  - [`ConversationAnalyzer`](src/dominusprime/agents/memory/experience/analyzer.py) - Analyzes conversations for learning opportunities
  - [`ExperienceExtractor`](src/dominusprime/agents/memory/experience/extractor.py) - Extracts patterns and experiences
  - [`SkillGenerator`](src/dominusprime/agents/memory/experience/skill_generator.py) - Generates markdown skill files
  - [`ExperienceSystem`](src/dominusprime/agents/memory/experience/system.py) - Main coordinator for experience learning
  - New database: `data/experiences.db` with experience storage and skill tracking

- **Multimodal Memory Fusion**: Process and retrieve images, audio, video alongside text memories
  - [`MediaProcessor`](src/dominusprime/agents/memory/multimodal/processor.py) - Processes images, audio, video, documents
  - [`MultimodalEmbedder`](src/dominusprime/agents/memory/multimodal/embedder.py) - Generates visual and text embeddings (CLIP, sentence-transformers)
  - [`MultimodalIndex`](src/dominusprime/agents/memory/multimodal/index.py) - Vector-based semantic search across multimodal content
  - New database: `data/multimodal.db` with media items and embeddings

- **Context-Aware Proactive Delivery**: Intelligently surface relevant memories at the right moment
  - [`ContextMonitor`](src/dominusprime/agents/memory/proactive/context_monitor.py) - Monitors conversation for trigger signals (task starts, errors, topic changes)
  - [`RelevanceScorer`](src/dominusprime/agents/memory/proactive/relevance_scorer.py) - Weighted relevance scoring (keywords, topics, temporal, patterns, context)
  - [`DeliveryManager`](src/dominusprime/agents/memory/proactive/delivery_manager.py) - 4 delivery strategies (aggressive, balanced, conservative, passive)
  - Multiple delivery methods: inline, notification, context, suggestion
  - Configurable timing: immediate, next turn, opportune moment

- **Shell Command Execution Security**: Risk analysis and approval system for shell commands
  - [`SecurityManager`](src/dominusprime/security/manager.py) - Central coordinator (singleton pattern)
  - [`RiskAnalyzer`](src/dominusprime/security/risk_analyzer.py) - Pattern-based risk detection with 50+ dangerous command patterns
  - 5 risk levels: SAFE, LOW, MEDIUM, HIGH, CRITICAL
  - [`ApprovalHandler`](src/dominusprime/security/approval_handler.py) - Async user approval with 120s timeout
  - [`ExecutionLogger`](src/dominusprime/security/execution_logger.py) - Complete audit trail logging
  - [`execute_shell_command_secure()`](src/dominusprime/agents/tools/shell_secure.py) - Secure wrapper for shell commands
  - New database: `data/security.db` with command execution logs and security events

- **Tool & Skills Permission System**: Granular control over tools and skills
  - Tool permission levels: ALLOW, PROMPT, DENY
  - Skills scanning on load (dangerous pattern detection)
  - Skills approval workflow
  - Rate limiting (commands per minute)
  - Permission inheritance and overrides

- **Configurable Security Levels**: 5 pre-configured security profiles
  - **OPEN** - No restrictions, full trust (development only)
  - **RELAXED** - Minimal checks, warnings only (prototyping)
  - **BALANCED** - Standard protection (recommended default)
  - **STRICT** - Enhanced security, frequent approvals (high security)
  - **PARANOID** - Maximum security, approve everything (critical systems)

- **CLI Commands**: New memory and security management commands
  - `dominusprime memory stats` - View memory statistics
  - `dominusprime memory list-experiences` - List stored experiences
  - `dominusprime memory search` - Search experiences by query
  - `dominusprime memory list-skills` - List generated skills
  - `dominusprime memory list-media` - List multimodal content
  - `dominusprime memory clear` - Clear all memory data
  - `dominusprime security status` - Show security configuration
  - `dominusprime security set-profile` - Set security profile
  - `dominusprime security audit` - View audit log
  - `dominusprime security stats` - Security statistics
  - `dominusprime security list-events` - List security events
  - `dominusprime security clear-logs` - Clear security logs

- **Database Infrastructure**:
  - [`DatabaseManager`](src/dominusprime/database/connection.py) - Multi-database support with 3 separate SQLite databases
  - Automatic schema migrations
  - Transaction support
  - Connection pooling and management

- **Documentation**:
  - [`docs/0.9.8-QUICK_START.md`](docs/0.9.8-QUICK_START.md) - Quick start guide
  - [`docs/0.9.8-API_REFERENCE.md`](docs/0.9.8-API_REFERENCE.md) - Complete API documentation
  - [`docs/0.9.8-CONFIGURATION_GUIDE.md`](docs/0.9.8-CONFIGURATION_GUIDE.md) - Configuration reference
  - [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Technical implementation overview

### Changed

- Updated version from 0.9.7 to 0.9.8
- Installer scripts now use Python 3.10 (required for dependency compatibility)
- Changed `agentscope-runtime[ext]` to `agentscope-runtime` (boxlite dependency issues)
- Installer scripts now use pip with `--seed` flag instead of uv pip
- Enhanced [`MemoryManager`](src/dominusprime/agents/memory/memory_manager.py) with hooks for experience distillation
- Security-first approach: all shell commands now route through security checks

### Fixed

- Python 3.12 compatibility issues with boxlite dependency
- Installer now works on all Windows machines
- Import naming consistency (`ExperienceSystem` instead of `ExperienceDistillationSystem`)

### Technical Details

**Implementation Stats:**
- 36 new files created
- ~5,200 lines of production code
- 3 database systems with 10+ tables
- 12 CLI commands added
- 5 security profiles with granular configuration

**Performance:**
- Embeddings: ~2KB per image embedding (512-dim vectors)
- Experiences: ~1KB per experience record
- Audit Logs: ~500 bytes per command execution
- Recommended limits: 10K experiences, 5K media items, 90-day audit retention

**Optional Dependencies:**
- `pillow` - Image processing
- `transformers` - CLIP visual embeddings
- `sentence-transformers` - Text embeddings
- `mutagen` - Audio metadata
- `opencv-python` - Video processing

**Note:** Systems gracefully degrade without optional dependencies.

### Migration Guide from 0.9.7

1. **Update Installation**:
   ```bash
   git checkout 0.9.8
   pip install -e .
   ```

2. **Initialize Databases** (automatic on first use):
   ```bash
   mkdir -p data
   # Databases auto-created: experiences.db, multimodal.db, security.db
   ```

3. **Configure Security** (optional):
   ```bash
   dominusprime security set-profile balanced
   ```

4. **Update Code** (if using shell commands directly):
   ```python
   # Old
   from dominusprime.agents.tools.shell import execute_shell_command
   
   # New (with security)
   from dominusprime.agents.tools.shell_secure import execute_shell_command_secure
   ```

## [0.9.7] - 2026-03-14

### Added

- **Windows Installer Support**: Complete Windows installer (.exe) solution for easy deployment
  - One-click Windows installer using Inno Setup
  - Automatic server launch and browser opening
  - Desktop icon and Start menu integration
  - Professional uninstaller
  
- **New Files**:
  - [`scripts/windows_launcher.py`](scripts/windows_launcher.py) - Launcher script that starts server and opens browser
  - [`scripts/build_windows_exe.spec`](scripts/build_windows_exe.spec) - PyInstaller configuration
  - [`scripts/windows_installer.iss`](scripts/windows_installer.iss) - Inno Setup installer script
  - [`scripts/build_windows_installer.bat`](scripts/build_windows_installer.bat) - Build script for Command Prompt
  - [`scripts/build_windows_installer.ps1`](scripts/build_windows_installer.ps1) - Build script for PowerShell
  - [`WINDOWS_INSTALLER.md`](WINDOWS_INSTALLER.md) - Complete documentation for the Windows installer
  - [`scripts/README_WINDOWS_BUILD.md`](scripts/README_WINDOWS_BUILD.md) - Quick start guide

### Changed

- Updated version from 0.9.6 to 0.9.7
- Enhanced [`README.md`](README.md) with Windows installer section

### Features

- Windows users can now install DominusPrime with a standard .exe installer
- Desktop shortcut automatically launches server and opens browser
- No manual command-line interaction required for end users
- Professional Windows application experience

## [0.9.6] - Previous Release

(Previous changelog entries...)
