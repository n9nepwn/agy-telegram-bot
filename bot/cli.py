#!/usr/bin/env python3
"""
AGY Telegram Bot — CLI

Usage:
    agy-telegram-bot setup               Interactive setup (create .env, configure everything)
    agy-telegram-bot start               Start the bot as a background daemon
    agy-telegram-bot stop                Stop the running bot
    agy-telegram-bot restart             Restart the bot
    agy-telegram-bot status              Show bot status (PID, uptime, memory)
    agy-telegram-bot logs                Tail the log file (live)
    agy-telegram-bot logs --clear        Clear the log file
    agy-telegram-bot auth                List authorized users
    agy-telegram-bot auth add <ID>       Add a Telegram User ID
    agy-telegram-bot auth remove <ID>    Remove a Telegram User ID
    agy-telegram-bot auth test           Test the current auth configuration
"""

import argparse
import os
import sys
import subprocess
import shutil
import getpass
import time
from pathlib import Path


# ─── Helpers ────────────────────────────────────────────────────────

def get_project_dir() -> str:
    """Find the project directory."""
    # Check if we're in the project dir
    if os.path.exists(os.path.join(os.getcwd(), "bot", "main.py")):
        return os.getcwd()

    # Check the installed location
    cli_file = os.path.abspath(__file__)
    project = os.path.dirname(os.path.dirname(cli_file))
    if os.path.exists(os.path.join(project, "bot", "main.py")):
        return project

    # Default fallback
    default = os.path.expanduser("~/agy-telegram-bot")
    if os.path.exists(default):
        return default

    return os.getcwd()


def load_env(project_dir: str) -> dict:
    """Load .env file into a dict."""
    env_file = os.path.join(project_dir, ".env")
    env = {}
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
    return env


def save_env(project_dir: str, env: dict):
    """Save env dict back to .env file, preserving comments."""
    env_file = os.path.join(project_dir, ".env")

    # Read existing file to preserve comments and order
    lines = []
    existing_keys = set()

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if key in env:
                        lines.append(f"{key}={env[key]}\n")
                        existing_keys.add(key)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

    # Add new keys that weren't in the file
    for key, value in env.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}\n")

    with open(env_file, "w") as f:
        f.writelines(lines)


def print_header(text: str):
    """Print a styled header."""
    width = max(len(text) + 4, 40)
    print(f"\n{'═' * width}")
    print(f"  {text}")
    print(f"{'═' * width}\n")


def print_success(text: str):
    print(f"  ✅ {text}")


def print_error(text: str):
    print(f"  ❌ {text}")


def print_info(text: str, **kwargs):
    print(f"  ℹ️  {text}", **kwargs)


def print_warn(text: str):
    print(f"  ⚠️  {text}")


def print_item(label: str, value: str, indent: int = 2):
    padding = " " * indent
    print(f"{padding}{'•':>3} {label}: {value}")


# ─── Commands ───────────────────────────────────────────────────────

def cmd_setup(args):
    """Interactive setup wizard."""
    project_dir = get_project_dir()

    print_header("🛠  AGY Telegram Bot — Setup")
    print(f"  Project directory: {project_dir}\n")

    env_file = os.path.join(project_dir, ".env")
    env = {}

    # Copy .env.example if .env doesn't exist
    if not os.path.exists(env_file):
        example = os.path.join(project_dir, ".env.example")
        if os.path.exists(example):
            shutil.copy2(example, env_file)
            print_info("Created .env from .env.example")
        else:
            # Create empty .env
            Path(env_file).touch()
            print_info("Created empty .env file")

    env = load_env(project_dir)

    # Step 1: Telegram Bot Token
    print("  ┌─ Step 1: Telegram Bot Token")
    print("  │")
    current_token = env.get("TELEGRAM_BOT_TOKEN", "")
    if current_token and current_token != "your_bot_token_here":
        masked = current_token[:8] + "..." + current_token[-4:] if len(current_token) > 12 else "***"
        print(f"  │  Current token: {masked}")
        change = input("  │  Change token? [y/N]: ").strip().lower()
        if change != "y":
            print("  │  → Keeping existing token")
        else:
            token = input("  │  Paste your bot token from @BotFather: ").strip()
            if token:
                env["TELEGRAM_BOT_TOKEN"] = token
                print_success("Token saved")
            else:
                print_warn("Skipped (empty input)")
    else:
        print("  │  No token configured.")
        print("  │  Create a bot: open Telegram → @BotFather → /newbot")
        print("  │")
        token = input("  │  Paste your bot token: ").strip()
        if token:
            env["TELEGRAM_BOT_TOKEN"] = token
            print_success("Token saved")
        else:
            print_error("Token is required! Run setup again when you have it.")
    print("  │")

    # Step 2: Allowed User IDs
    print("  ├─ Step 2: Authorized Users")
    print("  │")
    current_ids = env.get("ALLOWED_USER_IDS", "")
    if current_ids:
        print(f"  │  Current IDs: {current_ids}")
    else:
        print("  │  No users authorized yet.")
        print("  │  Find your ID: open Telegram → @userinfobot")
    print("  │")
    new_ids = input("  │  Telegram User IDs (comma-separated, Enter to keep): ").strip()
    if new_ids:
        env["ALLOWED_USER_IDS"] = new_ids
        print_success(f"Authorized users: {new_ids}")
    elif not current_ids:
        print_warn("No users set — bot will reject all messages!")
    print("  │")

    # Step 3: Default Model
    print("  ├─ Step 3: Default Model")
    print("  │")
    print("  │  Available models:")
    from bot.config import get_available_models
    print_info("Fetching models from AGY...", end="\r")
    models = get_available_models()
    
    if not models:
        print_error("Failed to fetch models or AGY is not authenticated.")
        print("  │  Run `agy --print hi` to verify your installation.")
    else:
        for i, name in enumerate(models, 1):
            print(f"  │    {i}. {name}")
        print("  │    0. Use AGY default")
        print("  │")

    current_model = env.get("DEFAULT_MODEL", "")
    if current_model:
        print(f"  │  Current: {current_model}")

    choice = input(f"  │  Choose model [0-{len(models)}, Enter to keep]: ").strip()
    if choice.isdigit():
        idx = int(choice)
        if idx == 0:
            env["DEFAULT_MODEL"] = ""
            print_info("Using AGY default model")
        elif 1 <= idx <= len(models):
            env["DEFAULT_MODEL"] = models[idx - 1]
            print_success(f"Model: {models[idx - 1]}")
    print("  │")

    # Step 4: Streaming
    print("  ├─ Step 4: Streaming Mode")
    print("  │")
    print("  │  Streaming = bot edits its message as the response comes in")
    current_streaming = env.get("ENABLE_STREAMING", "true")
    choice = input(f"  │  Enable streaming? [Y/n] (current: {current_streaming}): ").strip().lower()
    if choice == "n":
        env["ENABLE_STREAMING"] = "false"
        print_info("Streaming disabled")
    else:
        env["ENABLE_STREAMING"] = "true"
        print_success("Streaming enabled")
    print("  │")

    # Step 5: Log level
    print("  └─ Step 5: Log Level")
    print("  ")
    current_level = env.get("LOG_LEVEL", "INFO")
    choice = input(f"    Log level [DEBUG/INFO/WARNING/ERROR] (current: {current_level}): ").strip().upper()
    if choice in ("DEBUG", "INFO", "WARNING", "ERROR"):
        env["LOG_LEVEL"] = choice
    print()

    # Save
    save_env(project_dir, env)
    print_header("✅ Setup Complete")
    print("  Your configuration has been saved to .env")
    print()
    print("  Next steps:")
    print("    1. Start the bot:  agy-telegram-bot start")
    print("    2. Check status:   agy-telegram-bot status")
    print("    3. View logs:      agy-telegram-bot logs")
    print()


def cmd_start(args):
    """Start the bot daemon."""
    from bot.daemon import start_daemon, get_pid

    project_dir = get_project_dir()

    # Check if already running
    pid = get_pid()
    if pid:
        print_error(f"Bot is already running (PID {pid})")
        print_info("Use `agy-telegram-bot restart` to restart")
        return

    print_info("Starting AGY Telegram Bot...")
    success, message = start_daemon(project_dir)

    if success:
        print_success(message)
        print_info("View logs: agy-telegram-bot logs")
    else:
        print_error(message)


def cmd_stop(args):
    """Stop the bot daemon."""
    from bot.daemon import stop_daemon, get_pid

    pid = get_pid()
    if not pid:
        print_info("Bot is not running.")
        return

    print_info(f"Stopping bot (PID {pid})...")
    success, message = stop_daemon()

    if success:
        print_success(message)
    else:
        print_error(message)


def cmd_restart(args):
    """Restart the bot daemon."""
    from bot.daemon import stop_daemon, start_daemon, get_pid

    project_dir = get_project_dir()

    pid = get_pid()
    if pid:
        print_info(f"Stopping bot (PID {pid})...")
        stop_daemon()
        time.sleep(1)

    print_info("Starting AGY Telegram Bot...")
    success, message = start_daemon(project_dir)

    if success:
        print_success(message)
    else:
        print_error(message)


def cmd_status(args):
    """Show bot status."""
    from bot.daemon import get_status

    project_dir = get_project_dir()
    status = get_status()
    env = load_env(project_dir)

    print_header("📊 AGY Telegram Bot — Status")

    if status["running"]:
        print(f"  🟢 Bot is RUNNING")
        print()
        print_item("PID", str(status["pid"]))
        if "uptime_human" in status:
            print_item("Uptime", status["uptime_human"])
        if "memory_mb" in status:
            print_item("Memory", f"{status['memory_mb']} MB")
    else:
        print(f"  🔴 Bot is STOPPED")

    print()
    print(f"  ── Configuration ──")
    print()

    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if token and token != "your_bot_token_here":
        masked = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print_item("Bot Token", masked)
    else:
        print_item("Bot Token", "❌ NOT SET")

    user_ids = env.get("ALLOWED_USER_IDS", "")
    if user_ids:
        ids_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
        print_item("Authorized Users", f"{len(ids_list)} user(s) — [{user_ids}]")
    else:
        print_item("Authorized Users", "❌ NONE")

    print_item("Model", env.get("DEFAULT_MODEL", "(AGY default)") or "(AGY default)")
    print_item("Streaming", env.get("ENABLE_STREAMING", "true"))
    print_item("Log Level", env.get("LOG_LEVEL", "INFO"))
    print_item("Session Timeout", f"{env.get('SESSION_TIMEOUT_MINUTES', '60')} min")

    print()
    print(f"  ── Files ──")
    print()
    print_item("PID File", status["pid_file"])
    print_item("Log File", status["log_file"])
    if "log_size_mb" in status:
        print_item("Log Size", f"{status['log_size_mb']} MB")
    print_item("Project Dir", project_dir)
    print()


def cmd_logs(args):
    """Show bot logs."""
    from bot.daemon import DEFAULT_LOG_FILE

    if args.clear:
        if os.path.exists(DEFAULT_LOG_FILE):
            open(DEFAULT_LOG_FILE, "w").close()
            print_success("Log file cleared")
        else:
            print_info("No log file to clear")
        return

    if not os.path.exists(DEFAULT_LOG_FILE):
        print_info("No logs yet. Start the bot first: agy-telegram-bot start")
        return

    if args.lines:
        # Show last N lines
        try:
            result = subprocess.run(
                ["tail", f"-n{args.lines}", DEFAULT_LOG_FILE],
                capture_output=True,
                text=True,
            )
            print(result.stdout)
        except Exception as e:
            print_error(f"Failed to read logs: {e}")
    else:
        # Live tail
        print_info(f"Tailing {DEFAULT_LOG_FILE} (Ctrl+C to stop)\n")
        try:
            process = subprocess.Popen(
                ["tail", "-f", "-n", "50", DEFAULT_LOG_FILE],
            )
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            print("\n")
            print_info("Stopped log tailing")


def cmd_auth(args):
    """Manage authorized users."""
    project_dir = get_project_dir()
    env = load_env(project_dir)

    if args.auth_action == "add":
        _auth_add(project_dir, env, args.user_id)
    elif args.auth_action == "remove":
        _auth_remove(project_dir, env, args.user_id)
    elif args.auth_action == "test":
        _auth_test(env)
    else:
        _auth_list(env)


def _auth_list(env: dict):
    """List authorized users."""
    print_header("🔐 Authorized Users")

    user_ids = env.get("ALLOWED_USER_IDS", "")
    if not user_ids:
        print("  No users authorized.")
        print()
        print("  Add a user:    agy-telegram-bot auth add <TELEGRAM_USER_ID>")
        print("  Find your ID:  message @userinfobot on Telegram")
        print()
        return

    ids_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]

    for i, uid in enumerate(ids_list, 1):
        print(f"  {i}. Telegram ID: {uid}")

    print(f"\n  Total: {len(ids_list)} user(s)")
    print()
    print("  Add:     agy-telegram-bot auth add <ID>")
    print("  Remove:  agy-telegram-bot auth remove <ID>")
    print()


def _auth_add(project_dir: str, env: dict, user_id: str):
    """Add a user ID to the whitelist."""
    if not user_id:
        print_error("Specify a Telegram User ID: agy-telegram-bot auth add <ID>")
        return

    # Validate it's a number
    try:
        int(user_id)
    except ValueError:
        print_error(f"Invalid user ID: {user_id} (must be a number)")
        return

    current = env.get("ALLOWED_USER_IDS", "")
    ids_list = [uid.strip() for uid in current.split(",") if uid.strip()]

    if user_id in ids_list:
        print_warn(f"User {user_id} is already authorized")
        return

    ids_list.append(user_id)
    env["ALLOWED_USER_IDS"] = ",".join(ids_list)
    save_env(project_dir, env)

    print_success(f"User {user_id} added to whitelist")
    print_info(f"Total authorized users: {len(ids_list)}")
    print_warn("Restart the bot for changes to take effect: agy-telegram-bot restart")


def _auth_remove(project_dir: str, env: dict, user_id: str):
    """Remove a user ID from the whitelist."""
    if not user_id:
        print_error("Specify a Telegram User ID: agy-telegram-bot auth remove <ID>")
        return

    current = env.get("ALLOWED_USER_IDS", "")
    ids_list = [uid.strip() for uid in current.split(",") if uid.strip()]

    if user_id not in ids_list:
        print_error(f"User {user_id} is not in the whitelist")
        return

    ids_list.remove(user_id)
    env["ALLOWED_USER_IDS"] = ",".join(ids_list)
    save_env(project_dir, env)

    print_success(f"User {user_id} removed from whitelist")
    print_info(f"Remaining authorized users: {len(ids_list)}")
    print_warn("Restart the bot for changes to take effect: agy-telegram-bot restart")


def _auth_test(env: dict):
    """Test the current auth configuration."""
    print_header("🔍 Auth Configuration Test")

    # Check bot token
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if token and token != "your_bot_token_here":
        print_success(f"Bot token: configured ({token[:8]}...)")

        # Try to validate token with Telegram API
        try:
            import urllib.request
            import json

            url = f"https://api.telegram.org/bot{token}/getMe"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get("ok"):
                    bot_info = data["result"]
                    print_success(f"Bot name: @{bot_info.get('username', '?')}")
                    print_success(f"Bot display name: {bot_info.get('first_name', '?')}")
                else:
                    print_error("Token is invalid!")
        except Exception as e:
            print_warn(f"Could not validate token: {e}")
    else:
        print_error("Bot token: NOT SET")

    # Check user IDs
    user_ids = env.get("ALLOWED_USER_IDS", "")
    if user_ids:
        ids_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
        print_success(f"Authorized users: {len(ids_list)} configured")
    else:
        print_error("Authorized users: NONE — bot will reject all messages")

    # Check AGY SDK
    try:
        from google.antigravity import Agent, LocalAgentConfig
        print_success("AGY SDK: installed and importable")
    except ImportError:
        print_error("AGY SDK: not installed (run pip install google-antigravity)")

    # Check Google auth
    try:
        from google.auth import default as google_auth_default
        credentials, project = google_auth_default()
        print_success(f"Google Auth: configured (project: {project or 'default'})")
    except Exception as e:
        print_warn(f"Google Auth: {e}")

    print()


# ─── Main CLI ───────────────────────────────────────────────────────

BANNER = r"""
     _    ______   __  _____     _                                ____        _
    / \  / ___\ \ / / |_   _|__| | ___  __ _ _ __ __ _ _ __ ___ | __ )  ___ | |_
   / _ \| |  _ \ V /    | |/ _ \ |/ _ \/ _` | '__/ _` | '_ ` _ \|  _ \ / _ \| __|
  / ___ \ |_| | | |     | |  __/ |  __/ (_| | | | (_| | | | | | | |_) | (_) | |_
 /_/   \_\____| |_|     |_|\___|_|\___|\__, |_|  \__,_|_| |_| |_|____/ \___/ \__|
                                        |___/
"""


def main():
    parser = argparse.ArgumentParser(
        description="AGY Telegram Bot — CLI for managing your Antigravity Telegram bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agy-telegram-bot setup               Configure the bot interactively
  agy-telegram-bot start               Start the bot in background
  agy-telegram-bot status              Check if the bot is running
  agy-telegram-bot logs                Follow logs in real-time
  agy-telegram-bot auth add 123456     Authorize a Telegram user
  agy-telegram-bot restart             Restart the bot
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # setup
    sub_setup = subparsers.add_parser("setup", help="Interactive setup wizard")

    # start
    sub_start = subparsers.add_parser("start", help="Start the bot daemon")

    # stop
    sub_stop = subparsers.add_parser("stop", help="Stop the bot daemon")

    # restart
    sub_restart = subparsers.add_parser("restart", help="Restart the bot daemon")

    # status
    sub_status = subparsers.add_parser("status", help="Show bot status")

    # logs
    sub_logs = subparsers.add_parser("logs", help="View bot logs")
    sub_logs.add_argument("-n", "--lines", type=int, help="Show last N lines instead of live tail")
    sub_logs.add_argument("--clear", action="store_true", help="Clear the log file")

    # auth
    sub_auth = subparsers.add_parser("auth", help="Manage authorized users")
    auth_sub = sub_auth.add_subparsers(dest="auth_action")

    auth_list = auth_sub.add_parser("list", help="List authorized users")
    auth_add = auth_sub.add_parser("add", help="Add a user")
    auth_add.add_argument("user_id", help="Telegram User ID to add")
    auth_remove = auth_sub.add_parser("remove", help="Remove a user")
    auth_remove.add_argument("user_id", help="Telegram User ID to remove")
    auth_test = auth_sub.add_parser("test", help="Test auth configuration")

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    commands = {
        "setup": cmd_setup,
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "logs": cmd_logs,
        "auth": cmd_auth,
    }

    if args.command == "auth" and not args.auth_action:
        # Default to listing
        args.auth_action = None
        args.user_id = None

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
