#!/usr/bin/env bash
# dominusprime Installer
# Usage: curl -fsSL <your-url>/install.sh | bash
#    or: bash install.sh [--version X.Y.Z] [--source-dir DIR] [--extras extras]
#
# Installs dominusprime into ~/.dominusprime with a uv-managed Python environment.
# Installs AgentScope from the official upstream git repo first.
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
dominusprime_HOME="${dominusprime_HOME:-$HOME/.dominusprime}"
dominusprime_VENV="$dominusprime_HOME/venv"
dominusprime_BIN="$dominusprime_HOME/bin"
PYTHON_VERSION="3.12"
dominusprime_REPO="https://github.com/BattlescarZA/DominusPrime.git"

VERSION=""
SOURCE_DIR=""
EXTRAS=""

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    RED="\033[0;31m"
    RESET="\033[0m"
else
    BOLD="" GREEN="" YELLOW="" RED="" RESET=""
fi

info()  { printf "${GREEN}[dominusprime]${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}[dominusprime]${RESET} %s\n" "$*"; }
error() { printf "${RED}[dominusprime]${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            VERSION="$2"; shift 2 ;;
        --source-dir)
            SOURCE_DIR="$(cd "$2" && pwd)" || die "Directory not found: $2"
            shift 2 ;;
        --extras)
            EXTRAS="$2"; shift 2 ;;
        -h|--help)
            cat <<EOF
dominusprime Installer

Usage: bash install.sh [OPTIONS]

Options:
  --version <VER>       Install a specific version/tag from GitHub (e.g. v0.9.6)
  --source-dir <DIR>    Install from local source directory instead of GitHub
  --extras <EXTRAS>     Comma-separated optional extras (e.g. llamacpp,mlx)
  -h, --help            Show this help

Environment:
  dominusprime_HOME     Installation directory (default: ~/.dominusprime)

Note: Always installs AgentScope from official git repo first.
EOF
            exit 0 ;;
        *)
            die "Unknown option: $1 (try --help)" ;;
    esac
done

# ── OS check ──────────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Linux|Darwin) ;;
    *) die "Unsupported OS: $OS. This installer supports Linux and macOS only." ;;
esac

printf "${GREEN}[dominusprime]${RESET} Installing dominusprime into ${BOLD}%s${RESET}\n" "$dominusprime_HOME"

# ── Step 1: Ensure uv is available ───────────────────────────────────────────
ensure_uv() {
    if command -v uv &>/dev/null; then
        info "uv found: $(command -v uv)"
        return
    fi

    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            export PATH="$(dirname "$candidate"):$PATH"
            info "uv found: $candidate"
            return
        fi
    done

    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -f "$HOME/.local/bin/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.local/bin/env"
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    command -v uv &>/dev/null || die "Failed to install uv. Please install it manually: https://docs.astral.sh/uv/"
    info "uv installed successfully"
}

ensure_uv

# ── Step 2: Create / update virtual environment ──────────────────────────────
if [ -d "$dominusprime_VENV" ]; then
    info "Existing environment found, upgrading..."
else
    info "Creating Python $PYTHON_VERSION environment..."
fi

uv venv "$dominusprime_VENV" --python "$PYTHON_VERSION" --quiet

# Verify the venv was created
[ -x "$dominusprime_VENV/bin/python" ] || die "Failed to create virtual environment"
info "Python environment ready ($("$dominusprime_VENV/bin/python" --version))"

# ── Step 3: Install AgentScope from official git + dominusprime ──────────────
EXTRAS_SUFFIX=""
if [ -n "$EXTRAS" ]; then
    EXTRAS_SUFFIX="[$EXTRAS]"
fi

# Prepare console functions (copied from your original)
_CONSOLE_COPIED=0
_CONSOLE_AVAILABLE=0

prepare_console() {
    local repo_dir="$1"
    local console_src="$repo_dir/console/dist"
    local console_dest="$repo_dir/src/dominusprime/console"

    if [ -f "$console_dest/index.html" ]; then
        _CONSOLE_AVAILABLE=1
        return
    fi

    if [ -d "$console_src" ] && [ -f "$console_src/index.html" ]; then
        info "Copying console frontend assets..."
        mkdir -p "$console_dest"
        cp -R "$console_src/"* "$console_dest/"
        _CONSOLE_COPIED=1
        _CONSOLE_AVAILABLE=1
        return
    fi

    if [ ! -f "$repo_dir/console/package.json" ]; then
        warn "Console source not found — web UI won't be available."
        return
    fi

    if ! command -v npm &>/dev/null; then
        warn "npm not found — skipping console frontend build."
        return
    fi

    info "Building console frontend (npm ci && npm run build)..."
    (cd "$repo_dir/console" && npm ci && npm run build)
    if [ -f "$console_src/index.html" ]; then
        mkdir -p "$console_dest"
        cp -R "$console_src/"* "$console_dest/"
        _CONSOLE_COPIED=1
        _CONSOLE_AVAILABLE=1
        info "Console frontend built successfully"
        return
    fi

    warn "Console build completed but index.html not found — web UI unavailable."
}

cleanup_console() {
    local repo_dir="$1"
    if [ "$_CONSOLE_COPIED" = 1 ]; then
        rm -rf "$repo_dir/src/dominusprime/console/"*
    fi
}

# Install dominusprime (with dependencies including agentscope from pyproject.toml)
if [ -n "$SOURCE_DIR" ]; then
    info "Installing dominusprime from local source: $SOURCE_DIR"
    prepare_console "$SOURCE_DIR"
    uv pip install "${SOURCE_DIR}${EXTRAS_SUFFIX}" \
        --python "$dominusprime_VENV/bin/python" \
        --prerelease=allow
    cleanup_console "$SOURCE_DIR"
else
    info "Installing dominusprime from GitHub source..."
    CLONE_DIR="$(mktemp -d)"
    trap 'rm -rf "$CLONE_DIR"' EXIT

    if [ -n "$VERSION" ]; then
        info "Cloning version $VERSION..."
        git clone --depth 1 --branch "$VERSION" "$dominusprime_REPO" "$CLONE_DIR"
    else
        git clone --depth 1 "$dominusprime_REPO" "$CLONE_DIR"
    fi

    prepare_console "$CLONE_DIR"
    uv pip install "${CLONE_DIR}${EXTRAS_SUFFIX}" \
        --python "$dominusprime_VENV/bin/python" \
        --prerelease=allow
fi

# Verify the CLI entry point exists
[ -x "$dominusprime_VENV/bin/dominusprime" ] || die "Installation failed: dominusprime CLI not found in venv"
info "dominusprime installed successfully"

# Check console availability
if [ "$_CONSOLE_AVAILABLE" = 0 ]; then
    CONSOLE_CHECK="$("$dominusprime_VENV/bin/python" -c "import importlib.resources, dominusprime; p=importlib.resources.files('dominusprime')/'console'/'index.html'; print('yes' if p.is_file() else 'no')" 2>/dev/null || echo 'no')"
    if [ "$CONSOLE_CHECK" = "yes" ]; then
        _CONSOLE_AVAILABLE=1
    fi
fi

# ── Step 4: Create wrapper script ────────────────────────────────────────────
mkdir -p "$dominusprime_BIN"

cat > "$dominusprime_BIN/dominusprime" << 'WRAPPER'
#!/usr/bin/env bash
# dominusprime CLI wrapper — delegates to the uv-managed environment.
set -euo pipefail

dominusprime_HOME="${dominusprime_HOME:-$HOME/.dominusprime}"
REAL_BIN="$dominusprime_HOME/venv/bin/dominusprime"

if [ ! -x "$REAL_BIN" ]; then
    echo "Error: dominusprime environment not found at $dominusprime_HOME/venv" >&2
    echo "Please reinstall: curl -fsSL <install-url> | bash" >&2
    exit 1
fi

exec "$REAL_BIN" "$@"
WRAPPER

chmod +x "$dominusprime_BIN/dominusprime"
info "Wrapper created at $dominusprime_BIN/dominusprime"

# ── Step 5: Update PATH in shell profile ─────────────────────────────────────
PATH_ENTRY="export PATH=\"\$HOME/.dominusprime/bin:\$PATH\""

add_to_profile() {
    local profile="$1"
    if [ -f "$profile" ] && grep -qF '.dominusprime/bin' "$profile"; then
        return 0
    fi
    if [ -f "$profile" ] || [ "$2" = "create" ]; then
        printf '\n# dominusprime\n%s\n' "$PATH_ENTRY" >> "$profile"
        info "Updated $profile"
        return 0
    fi
    return 1
}

UPDATED_PROFILE=false

case "$OS" in
    Darwin)
        add_to_profile "$HOME/.zshrc" "create" && UPDATED_PROFILE=true
        add_to_profile "$HOME/.bash_profile" "no-create" || true
        ;;
    Linux)
        add_to_profile "$HOME/.bashrc" "create" && UPDATED_PROFILE=true
        add_to_profile "$HOME/.zshrc" "no-create" || true
        ;;
esac

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}${BOLD}dominusprime installed successfully!${RESET}\n"
echo ""

printf "  Install location:  ${BOLD}%s${RESET}\n" "$dominusprime_HOME"
printf "  Python:            ${BOLD}%s${RESET}\n" "$("$dominusprime_VENV/bin/python" --version 2>&1)"
if [ "$_CONSOLE_AVAILABLE" = 1 ]; then
    printf "  Console (web UI):  ${GREEN}available${RESET}\n"
else
    printf "  Console (web UI):  ${YELLOW}not available${RESET}\n"
    echo "                     Install Node.js and re-run to enable the web UI."
fi
echo ""

if [ "$UPDATED_PROFILE" = true ]; then
    echo "Activating dominusprime in current shell..."
    export PATH="$dominusprime_BIN:$PATH"
    echo ""
fi

echo "You can now run:"
echo ""
printf "  ${BOLD}dominusprime init${RESET}       # first-time setup\n"
printf "  ${BOLD}dominusprime app${RESET}        # start dominusprime\n"
echo ""
printf "To upgrade:        re-run this installer\n"
printf "To uninstall:      ${BOLD}dominusprime uninstall${RESET}\n"
