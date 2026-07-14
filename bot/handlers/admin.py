"""
Admin handlers — bot status, session restart.
"""

import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status — Show bot health, active sessions, and uptime.
    """
    agent_manager = context.bot_data["agent_manager"]
    start_time = context.bot_data.get("start_time", time.time())

    uptime_seconds = time.time() - start_time
    uptime_hours = uptime_seconds / 3600
    uptime_minutes = (uptime_seconds % 3600) / 60

    all_sessions = agent_manager.get_all_sessions_info()

    lines = [
        "🟢 **Bot Status**\n",
        f"⏱ Uptime : {int(uptime_hours)}h {int(uptime_minutes)}m",
        f"👥 Sessions actives : {all_sessions['active_sessions']}",
    ]

    if all_sessions["sessions"]:
        lines.append("\n**Sessions :**")
        for uid, info in all_sessions["sessions"].items():
            status = "🔄" if info.get("is_busy") else "✅"
            lines.append(
                f"  {status} User `{uid}` — `{info['model']}` "
                f"({info['message_count']} msgs, idle {info['idle_minutes']}m)"
            )

    lines.append(f"\n🔧 Version : 1.0.0")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /restart — Restart the current AGY session (same model, fresh context).
    """
    user_id = update.effective_user.id
    agent_manager = context.bot_data["agent_manager"]
    db = context.bot_data.get("db")

    # End current conversation in DB
    if db:
        conv = await db.get_active_conversation(user_id)
        if conv:
            await db.end_conversation(conv["id"])

    # Restart session
    result = await agent_manager.new_session(user_id)

    # Create new conversation in DB
    if db:
        session_info = agent_manager.get_session_info(user_id)
        model = session_info["model"] if session_info else ""
        await db.create_conversation(user_id, model)

    await update.message.reply_text(
        f"🔄 Session redémarrée !\n{result}",
        parse_mode="Markdown",
    )
    logger.info(f"User {user_id} restarted their session")
