#!/usr/bin/env bash
#
# AGY Telegram Bot — Uninstaller
#
# Removes the global CLI command and optionally the virtual environment.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${BLUE}ℹ${NC}  $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠️${NC}  $1"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
WRAPPER_PATH="/usr/local/bin/agy-telegram-bot"

echo -e "\n${BOLD}AGY Telegram Bot — Uninstall${NC}\n"

# Stop the bot if running
if [ -f "$HOME/.agy-telegram-bot/bot.pid" ]; then
    PID=$(cat "$HOME/.agy-telegram-bot/bot.pid" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        info "Stopping running bot (PID $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 1
        success "Bot stopped"
    fi
    rm -f "$HOME/.agy-telegram-bot/bot.pid"
fi

# Remove global command
if [ -f "$WRAPPER_PATH" ]; then
    if [ -w "$WRAPPER_PATH" ] || [ "$(id -u)" -eq 0 ]; then
        rm -f "$WRAPPER_PATH"
    else
        sudo rm -f "$WRAPPER_PATH" 2>/dev/null || true
    fi
    success "Removed $WRAPPER_PATH"
else
    info "No global command found at $WRAPPER_PATH"
fi

# Ask about venv
read -p "  Remove virtual environment (.venv)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$PROJECT_DIR/.venv"
    success "Virtual environment removed"
fi

# Ask about data
read -p "  Remove bot data (logs, database)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.agy-telegram-bot"
    rm -rf "$PROJECT_DIR/data"
    success "Bot data removed"
fi

echo ""
success "Uninstall complete"
echo ""
