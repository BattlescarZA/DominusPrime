# DominusPrime Skills System

## Overview

The Skills System provides a structured way to store, manage, and utilize procedural knowledge for AI agents. Skills are reusable, shareable units of knowledge that guide agents through specific tasks, from debugging Python code to conducting web research.

## Architecture

### Directory Structure

Skills are stored in `~/.dominusprime/skills/` with the following organization:

```
~/.dominusprime/skills/
├── category-name/
│   └── skill-name/
│       ├── SKILL.md           # Main skill content (YAML frontmatter + Markdown)
│       ├── references/        # Supporting documentation
│       ├── templates/         # Reusable templates
│       ├── scripts/           # Helper scripts
│       └── assets/            # Images, diagrams, etc.
└── uncategorized/
    └── skill-name/
        └── SKILL.md
```

**Example:**
```
~/.dominusprime/skills/
├── development/
│   ├── python-debugging/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── pdb-quick-reference.md
│   └── git-workflow/
│       └── SKILL.md
├── research/
│   └── web-research/
│       ├── SKILL.md
│       └── references/
│           └── search-operators-cheatsheet.md
└── system/
    └── log-analysis/
        └── SKILL.md
```

### Skill Format

Each skill is defined in a `SKILL.md` file with YAML frontmatter followed by Markdown content:

```markdown
---
name: skill-name
description: Brief description of what this skill does
platforms: [linux, macos, windows]
required_tools: [execute_shell_command, read_file]
required_toolsets: []
tags: [python, debugging, development]
author: DominusPrime
version: 1.0.0
---

# Skill Title

## Overview

Brief overview of the skill...

## When to Use

- Scenario 1
- Scenario 2

## Steps

1. Step one
2. Step two
...
```

### Frontmatter Schema

**Required Fields:**
- `name` (string): Skill identifier (lowercase, alphanumeric, hyphens, dots, underscores)
- `description` (string): Brief description (max 1024 characters)

**Optional Fields:**
- `platforms` (list): Compatible platforms (`linux`, `macos`, `windows`)
- `required_tools` (list): Tools needed to execute this skill
- `required_toolsets` (list): Tool sets required
- `tags` (list): Searchable tags
- `author` (string): Skill creator
- `version` (string): Version number
- `deprecated` (boolean): Mark as deprecated
- `replaces` (string): Name of skill this replaces

## Agent Tools

### skill_manage Tool

Agent-facing tool for creating and managing skills autonomously.

**Actions:**
- `create`: Create new skill with directory structure
- `edit`: Replace entire SKILL.md content
- `patch`: Targeted find-and-replace within files
- `delete`: Remove skill entirely
- `write_file`: Add/overwrite supporting files
- `remove_file`: Remove supporting files

**Examples:**

```python
# Create a new skill
await skill_manage(
    action="create",
    name="git-workflow",
    category="development",
    content="""---
name: git-workflow
description: Best practices for Git version control workflow
platforms: [linux, macos, windows]
required_tools: [execute_shell_command]
---

# Git Workflow Skill

## Common Commands

git status
git add .
git commit -m "message"
git push
"""
)

# Edit existing skill
await skill_manage(
    action="edit",
    name="git-workflow",
    content="<updated content>"
)

# Patch a section
await skill_manage(
    action="patch",
    name="git-workflow",
    find="## Common Commands",
    replace="## Essential Git Commands"
)

# Add reference file
await skill_manage(
    action="write_file",
    name="git-workflow",
    file_path="references/git-cheatsheet.md",
    content="# Git Cheatsheet\n..."
)

# Delete skill
await skill_manage(
    action="delete",
    name="git-workflow"
)
```

### skills Tool

Agent-facing tool for discovering and viewing skills.

**Actions:**
- `list`: List all available skills
- `view`: View skill content
- `search`: Search skills by query
- `categories`: Get list of categories

**Examples:**

```python
# List all skills
await skills(action="list")

# List skills in category
await skills(action="list", category="development")

# View a skill
await skills(action="view", name="python-debugging")

# View with supporting files
await skills(
    action="view",
    name="python-debugging",
    include_supporting_files=True
)

# Search for skills
await skills(action="search", query="debug")

# Search in content too
await skills(
    action="search",
    query="pdb",
    search_content=True
)

# Get categories
await skills(action="categories")
```

## Security

### Security Scanning

All skills are automatically scanned for dangerous patterns when created or modified:

**Blocked Patterns:**
- Subprocess execution (`subprocess.run`, `os.system`)
- Code evaluation (`eval()`, `exec()`)
- Directory traversal (`../`)
- Network operations (`requests.*`, `socket.*`)
- Dangerous imports

Skills containing these patterns will be rejected with a security error.

### Validation

**Name Validation:**
- Lowercase only
- Alphanumeric, hyphens, dots, underscores
- Max 64 characters
- Filesystem-safe and URL-friendly

**Category Validation:**
- Same rules as name validation
- Optional (uncategorized if not provided)

**Frontmatter Validation:**
- Must contain valid YAML
- Required fields: `name`, `description`
- Platform compatibility checked
- Description max 1024 characters

## Platform Compatibility

Skills can specify compatible platforms:

```yaml
platforms: [linux, macos, windows]  # All platforms
platforms: [linux, macos]            # Unix-like only
platforms: [windows]                 # Windows only
platforms: []                        # Platform-agnostic
```

Skills incompatible with the current platform are filtered out during listing.

## Advanced Features (Phase 2)

### Slash Commands

Quick skill loading using slash commands in conversation:

```
/python-debugging
/web-research
/log-analysis
```

When you type `/skill-name`, the system:
1. Detects the command pattern
2. Loads the skill content
3. Formats it for the agent
4. Injects it into the conversation context

This provides instant access to procedural knowledge without manual skill_manage calls.

### Context Management

Automatic context management with provider detection:

**Features:**
- **Auto-detection**: Detects context length from model providers
- **Default**: 128k tokens for unknown models
- **Compression trigger**: Activates at 90% context usage
- **User-configurable**: Override via configuration file
- **Priority chain**: Explicit > User config > API > Known models > Default

**Supported Providers:**
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude models)
- Google (Gemini models)
- And 30+ pre-configured models

**Usage:**
```python
from dominusprime.agents.utils.context_manager import ContextManager

manager = ContextManager(
    model_name="gpt-4-turbo",
    provider="openai",
    max_tokens=128000  # Optional override
)

# Check if compression needed
if manager.should_compress(current_tokens=115000):
    target = manager.get_compression_target()  # Returns 64000 (half)
    # Perform compression...
```

### Advanced Caching

LRU (Least Recently Used) cache with disk persistence:

**Features:**
- **Automatic eviction**: Removes oldest items when max size exceeded
- **TTL support**: Time-to-live for cache entries
- **Disk persistence**: Survives process restarts
- **Thread-safe**: Concurrent access with RLock
- **Compute-once pattern**: `get_or_set` with factory function

**Usage:**
```python
from dominusprime.agents.utils.advanced_cache import LRUCache

cache = LRUCache(
    max_size=100,
    ttl=3600,  # 1 hour
    disk_path="cache.json",
    auto_persist=True
)

# Simple get/set
cache.set("key", "value")
value = cache.get("key")

# Compute-once pattern
value = cache.get_or_set("expensive_key", lambda: expensive_computation())

# Statistics
stats = cache.get_stats()
# {"hits": 42, "misses": 8, "hit_rate": 0.84, "size": 50}
```

### Skill Auto-Generation

Automatically generate skills from successful task executions:

**How It Works:**
1. **Trajectory Tracking**: Monitors tool usage patterns
2. **Pattern Detection**: Identifies repeated procedures (MD5 + Jaccard similarity)
3. **Template Generation**: Creates YAML frontmatter + Markdown content
4. **Approval Workflow**: Interactive or auto-approve mode
5. **Automatic Storage**: Saves approved skills to disk

**Example:**
```python
from dominusprime.agents.utils.skill_autogen_manager import SkillAutoGenManager

manager = SkillAutoGenManager(
    storage_dir=Path("~/.dominusprime/skills"),
    auto_approve=False,  # Require user approval
    min_tools=3  # Minimum complexity threshold
)

# Start tracking
manager.start_task("Debug Python application")

# Record tool calls
manager.record_tool("execute_shell_command", {"command": "python app.py"}, result, success=False)
manager.record_tool("read_file", {"path": "app.py"}, content, success=True)
manager.record_tool("write_to_file", {"path": "app.py"}, None, success=True)
manager.record_tool("execute_shell_command", {"command": "python app.py"}, result, success=True)

# Complete and propose skill
skill = await manager.complete_task(success=True, outcome="Fixed import error")

if skill:
    print(f"Skill created: {skill['name']}")
    print(f"Category: {skill['category']}")
    print(f"Path: ~/.dominusprime/skills/{skill['category']}/{skill['name']}/SKILL.md")
```

**Skill Worthiness Criteria:**
- Minimum 3 tool calls (configurable)
- Successful completion
- Either repeated pattern (seen 2+ times) OR complex workflow (5+ tools)

**Pattern Detection:**
- **Exact matching**: MD5 signature of tool sequence
- **Fuzzy matching**: Jaccard similarity for similar workflows
- **Threshold**: 0.7 similarity score
- **Persistence**: Pattern history saved to disk

**Generated Skill Structure:**
```yaml
---
name: debug-python-application
description: Debug Python application error
category: development
platforms:
  - linux
  - darwin
  - windows
required_tools:
  - execute_shell_command
  - read_file
  - write_to_file
tags:
  - auto-generated
  - trajectory-based
created_from: task execution pattern
---

# Debug Python Application

## Overview
This skill was auto-generated from a successful task execution.

## Steps
1. Execute: `python app.py`
2. Read file: `app.py`
3. Write file: `app.py`
4. Execute: `python app.py`

## Outcome
Fixed import error and application runs successfully
```

## CLI Commands

### dominusprime skills list

List all available skills.

```bash
# List all skills
dominusprime skills list

# List skills in category
dominusprime skills list --category development

# Include disabled skills
dominusprime skills list --include-disabled

# Show all platforms
dominusprime skills list --no-platform-filter
```

### dominusprime skills view

View skill content.

```bash
# View skill
dominusprime skills view python-debugging

# View with supporting files
dominusprime skills view python-debugging --include-files
```

### dominusprime skills search

Search for skills.

```bash
# Search by name/description
dominusprime skills search debug

# Search in content
dominusprime skills search pdb --content

# Search in category
dominusprime skills search debug --category development
```

### dominusprime skills create

Create a new skill interactively.

```bash
# Interactive creation
dominusprime skills create

# From template
dominusprime skills create --template debugging
```

### dominusprime skills edit

Edit an existing skill.

```bash
# Edit in default editor
dominusprime skills edit python-debugging

# Edit frontmatter only
dominusprime skills edit python-debugging --frontmatter
```

### dominusprime skills delete

Delete a skill.

```bash
# Delete skill
dominusprime skills delete python-debugging

# Force delete without confirmation
dominusprime skills delete python-debugging --force
```

### dominusprime skills categories

List all categories.

```bash
dominusprime skills categories
```

### dominusprime skills disable

Disable a skill without deleting it.

```bash
dominusprime skills disable python-debugging
```

### dominusprime skills enable

Re-enable a disabled skill.

```bash
dominusprime skills enable python-debugging
```

### dominusprime skills export

Export skill to file.

```bash
# Export single skill
dominusprime skills export python-debugging -o skill.tar.gz

# Export category
dominusprime skills export --category development -o dev-skills.tar.gz

# Export all
dominusprime skills export --all -o all-skills.tar.gz
```

### dominusprime skills import

Import skill from file.

```bash
# Import skill
dominusprime skills import skill.tar.gz

# Import with different name
dominusprime skills import skill.tar.gz --name new-name

# Import to category
dominusprime skills import skill.tar.gz --category custom
```

## Configuration

Skills configuration is in `~/.dominusprime/config.yaml`:

```yaml
skills:
  # Directory where skills are stored
  directory: ~/.dominusprime/skills
  
  # List of disabled skills (by name)
  disabled:
    - outdated-skill
    - deprecated-skill
  
  # Auto-generation settings
  auto_generate:
    enabled: true
    min_trajectory_length: 5  # Minimum steps to suggest skill
    suggestion_threshold: 2    # Suggest after N similar tasks
  
  # Security settings
  security:
    scan_enabled: true
    allow_subprocess: false
    allow_network: false
  
  # Cache settings
  cache:
    enabled: true
    ttl: 3600  # Cache TTL in seconds
    max_size: 100  # Max cached skills
```

## Best Practices

### Writing Skills

1. **Clear Structure**: Use headings and bullet points
2. **Actionable Steps**: Provide concrete, executable steps
3. **Tool Integration**: Show how to use DominusPrime tools
4. **Examples**: Include code examples and command samples
5. **Context**: Explain when and why to use the skill
6. **References**: Add supporting documentation in `references/`
7. **Prerequisites**: List required tools and knowledge
8. **Cross-references**: Link to related skills

### Skill Organization

1. **Categories**: Use logical categories (development, research, system, etc.)
2. **Naming**: Use descriptive, kebab-case names
3. **Versioning**: Increment version on significant changes
4. **Tags**: Add relevant tags for discoverability
5. **Dependencies**: Document required tools and toolsets

### Maintenance

1. **Review Regularly**: Update skills as tools/practices evolve
2. **Test Skills**: Verify skills work as documented
3. **Deprecation**: Mark outdated skills as deprecated
4. **Migration**: When replacing skills, note in `replaces` field
5. **Documentation**: Keep examples current

## Auto-generation (Planned)

### How It Works

1. **Trajectory Tracking**: Agent's actions are recorded during task execution
2. **Pattern Detection**: System identifies repeated action sequences
3. **Skill Suggestion**: After N similar tasks, suggest creating skill
4. **Template Generation**: Auto-generate skill from trajectory
5. **User Approval**: Human reviews and approves skill
6. **Refinement**: Agent improves skill based on usage

### Trajectory Example

```python
# Task: Debug Python script
# Trajectory:
1. read_file("script.py")
2. execute_shell_command("python script.py")  # Error observed
3. execute_shell_command("python -m pdb script.py")
4. # Fixed issue
5. execute_shell_command("python script.py")  # Success

# Generated Skill:
name: debug-python-script
description: Debug a Python script using pdb
steps:
  1. Read the problematic script
  2. Run to observe error
  3. Use pdb debugger to investigate
  4. Fix issue
  5. Verify fix
```

## Integration Points

### System Prompt

Skills index is injected into agent system prompt:

```
Available Skills:
- python-debugging: Debug Python applications (development)
- web-research: Conduct effective web research (research)
- log-analysis: Analyze system logs (system)

To view a skill: await skills(action="view", name="skill-name")
```

### Slash Commands

Skills can be invoked directly:

```
User: /python-debugging

Agent: *Loading python-debugging skill*
[Skill content displayed]
How can I help you debug your Python code?
```

### Memory Integration

Skills used in conversations are logged for:
- Usage analytics
- Skill effectiveness tracking
- Auto-improvement suggestions

## API Reference

### skill_utils Module

Core utilities for skills system.

```python
from dominusprime.agents.utils.skill_utils import (
    parse_frontmatter,
    skill_matches_platform,
    validate_skill_name,
    validate_skill_category,
    validate_skill_frontmatter,
    get_skills_directory,
    find_skill_by_name,
    iter_skill_files,
    build_skill_path,
    get_disabled_skill_names,
)

# Parse frontmatter
frontmatter, body = parse_frontmatter(content)

# Check platform compatibility
is_compatible = skill_matches_platform(frontmatter)

# Validate name
error = validate_skill_name("my-skill")  # None if valid

# Find skill
skill_path = find_skill_by_name("python-debugging")

# Iterate all skills
for skill_path in iter_skill_files(get_skills_directory()):
    print(skill_path)
```

### Error Handling

```python
from dominusprime.agents.tools import skill_manage

result = await skill_manage(action="create", name="test", content="...")
result_dict = json.loads(result)

if not result_dict["success"]:
    print(f"Error: {result_dict['message']}")
else:
    print(f"Success: {result_dict['message']}")
    print(f"Path: {result_dict['path']}")
```

## Examples

See `examples/skills/` for complete skill examples:

- `development/python-debugging/`: Python debugging guide
- `research/web-research/`: Web research methodology
- `system/log-analysis/`: Log analysis techniques

## Roadmap

### Week 1: Core Infrastructure ✅ (COMPLETED)
- [x] Skill utilities
- [x] Skill manager tool
- [x] Skills discovery tool
- [x] Security scanning
- [x] Example skills

### Week 2: System Integration ✅ (COMPLETED)
- [x] CLI commands
- [x] System prompt integration
- [x] Slash commands for quick skill loading (`/skill-name`)
- [x] Advanced caching with LRU eviction and disk persistence
- [x] Context management with provider detection (128k default, 90% compression)
- [x] Platform filtering

### Week 3: Auto-generation ✅ (COMPLETED)
- [x] Trajectory tracking for task execution patterns
- [x] Pattern detection (MD5 signatures + Jaccard similarity)
- [x] Template generation from successful workflows
- [x] User approval workflow with auto-approve mode
- [x] Automatic skill creation and file storage

### Week 4: Polish ✅ (COMPLETED)
- [x] Comprehensive integration testing (20/20 tests passing)
- [x] Performance optimization (caching, LRU, thread-safe operations)
- [x] Documentation completion
- [x] Full end-to-end workflow validation
- [x] Edge case handling and error recovery

## Contributing

### Creating Skills

1. Use skill_manage tool or CLI
2. Follow frontmatter schema
3. Include clear, actionable steps
4. Add references and examples
5. Test thoroughly
6. Submit for review

### Skill Guidelines

- **Clarity**: Clear, concise language
- **Completeness**: Cover all common scenarios
- **Correctness**: Verify all commands and examples
- **Currency**: Keep content up-to-date
- **Citation**: Attribute sources appropriately

## Support

For issues or questions:

1. Check existing skills for examples
2. Review documentation
3. Check GitHub issues
4. Contact maintainers

## License

Skills are part of DominusPrime and follow the same license. Individual skills may have additional attribution requirements noted in their frontmatter.
