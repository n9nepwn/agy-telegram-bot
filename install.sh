#!/usr/bin/env bash
#
# AGY Telegram Bot — One-line installer
#
# Usage:
#   git clone <repo> && cd agy-telegram-bot && ./install.sh
#
# What it does:
#   1. Creates a Python virtual environment
#   2. Installs all dependencies
#   3. Installs the `agy-telegram-bot` CLI command globally
#   4. Runs the setup wizard
#

set -e

# ── Colors ──────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# ── Helpers ─────────────────────────────────────────────────────────

info()    { echo -e "${BLUE}ℹ${NC}  $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠️${NC}  $1"; }
error()   { echo -e "${RED}❌${NC} $1"; }
step()    { echo -e "\n${CYAN}${BOLD}[$1/$TOTAL_STEPS]${NC} ${BOLD}$2${NC}"; }

# ── Banner ──────────────────────────────────────────────────────────

echo -e "${CYAN}"
cat << 'EOF'
     _    ______   __  _____     _                                ____        _
    / \  / ___\ \ / / |_   _|__| | ___  __ _ _ __ __ _ _ __ ___ | __ )  ___ | |_
   / _ \| |  _ \ V /    | |/ _ \ |/ _ \/ _` | '__/ _` | '_ ` _ \|  _ \ / _ \| __|
  / ___ \ |_| | | |     | |  __/ |  __/ (_| | | | (_| | | | | | | |_) | (_) | |_
 /_/   \_\____| |_|     |_|\___|_|\___|\__, |_|  \__,_|_| |_| |_|____/ \___/ \__|
                                        |___/
EOF
echo -e "${NC}"
echo -e "${DIM}  Telegram ↔ Google Antigravity Bridge${NC}"
echo ""

TOTAL_STEPS=4
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
WRAPPER_PATH="/usr/local/bin/agy-telegram-bot"

# ── Step 1: Check prerequisites ─────────────────────────────────────

step 1 "Checking prerequisites..."

# Check Python 3.11+
if command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
    PY_VERSION=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        success "Python $PY_VERSION found at $PYTHON"
    else
        error "Python 3.11+ required, found $PY_VERSION"
        exit 1
    fi
else
    error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check pip
if ! $PYTHON -m pip --version &> /dev/null; then
    error "pip not found. Please install pip for Python 3"
    exit 1
fi

# Check venv module
if ! $PYTHON -m venv --help &> /dev/null 2>&1; then
    warn "venv module not found, installing..."
    apt-get install -y python3-venv 2>/dev/null || {
        error "Could not install python3-venv. Please install it manually."
        exit 1
    }
fi

success "All prerequisites met"

# ── Step 2: Create virtual environment ───────────────────────────────

step 2 "Setting up virtual environment..."

VENV_DIR="$PROJECT_DIR/.venv"

if [ -d "$VENV_DIR" ]; then
    info "Virtual environment already exists, updating..."
else
    $PYTHON -m venv "$VENV_DIR"
    success "Virtual environment created at .venv/"
fi

# Activate and install
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q 2>/dev/null
pip install -e "$PROJECT_DIR" -q 2>&1 | grep -E "(Successfully|ERROR)" || true

success "Dependencies installed"

# ── Step 3: Install global CLI command ───────────────────────────────

step 3 "Installing 'agy-telegram-bot' command..."

# Create wrapper script that auto-activates venv
WRAPPER_CONTENT="#!/usr/bin/env bash
# Auto-generated wrapper for agy-telegram-bot
# Project: $PROJECT_DIR
exec \"$VENV_DIR/bin/agy-telegram-bot\" \"\$@\"
"

# Try to install to /usr/local/bin (may need sudo)
if [ -w "/usr/local/bin" ] || [ "$(id -u)" -eq 0 ]; then
    echo "$WRAPPER_CONTENT" > "$WRAPPER_PATH"
    chmod +x "$WRAPPER_PATH"
    success "Command installed at $WRAPPER_PATH"
else
    # Try with sudo
    echo "$WRAPPER_CONTENT" | sudo tee "$WRAPPER_PATH" > /dev/null 2>&1 && \
        sudo chmod +x "$WRAPPER_PATH" 2>/dev/null

    if [ $? -eq 0 ]; then
        success "Command installed at $WRAPPER_PATH (via sudo)"
    else
        warn "Could not install to /usr/local/bin"
        info "You can still use: $VENV_DIR/bin/agy-telegram-bot"

        # Add alias suggestion
        SHELL_RC=""
        if [ -f "$HOME/.zshrc" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_RC="$HOME/.bashrc"
        fi

        if [ -n "$SHELL_RC" ]; then
            echo ""
            info "Or add this alias to your $SHELL_RC:"
            echo -e "  ${DIM}echo 'alias agy-telegram-bot=\"$VENV_DIR/bin/agy-telegram-bot\"' >> $SHELL_RC${NC}"
        fi
    fi
fi

# ── Step 4: Verify installation ──────────────────────────────────────

step 4 "Verifying installation..."

# Test the command
if command -v agy-telegram-bot &> /dev/null; then
    success "'agy-telegram-bot' command is available globally"
elif [ -f "$VENV_DIR/bin/agy-telegram-bot" ]; then
    success "'agy-telegram-bot' available via venv"
fi

# Test core imports
$VENV_DIR/bin/python3 -c "
from bot.config import Settings
from bot.agent import AGYSessionManager
from google.antigravity import Agent
from telegram.ext import ApplicationBuilder
print('All imports OK')
" 2>/dev/null && success "All Python imports working" || warn "Some imports failed (may need google auth)"

# ── Done ─────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Installation complete!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Next steps:${NC}"
echo ""
echo -e "  ${CYAN}1.${NC} Configure the bot:"
echo -e "     ${BOLD}agy-telegram-bot setup${NC}"
echo ""
echo -e "  ${CYAN}2.${NC} Start the bot:"
echo -e "     ${BOLD}agy-telegram-bot start${NC}"
echo ""
echo -e "  ${CYAN}3.${NC} Check status:"
echo -e "     ${BOLD}agy-telegram-bot status${NC}"
echo ""
echo -e "  ${DIM}All commands: agy-telegram-bot --help${NC}"
echo ""

# ── Offer to run setup ───────────────────────────────────────────────

read -p "  Run setup wizard now? [Y/n] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    exec agy-telegram-bot setup
fi
