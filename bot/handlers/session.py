"""
Session management handlers — new session, history, clear.
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.formatting import truncate

logger = logging.getLogger(__name__)


async def new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /new — Start a fresh conversation (reset AGY context).
    """
    user_id = update.effective_user.id
    agent_manager = context.bot_data["agent_manager"]
    db = context.bot_data.get("db")

    # End current conversation in DB
    if db:
        conv = await db.get_active_conversation(user_id)
        if conv:
            await db.end_conversation(conv["id"])

    # Create new AGY session
    result = await agent_manager.new_session(user_id)

    # Create new conversation in DB
    if db:
        session_info = agent_manager.get_session_info(user_id)
        model = session_info["model"] if session_info else ""
        await db.create_conversation(user_id, model)

    await update.message.reply_text(result, parse_mode="Markdown")
    logger.info(f"User {user_id} started a new session")


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /history — Show recent messages from the current conversation.
    """
    user_id = update.effective_user.id
    db = context.bot_data.get("db")

    if not db:
        await update.message.reply_text("❌ Database not available.")
        return

    conv = await db.get_active_conversation(user_id)
    if not conv:
        await update.message.reply_text(
            "ℹ️ No active conversation.\nSend a message to start one!"
        )
        return

    messages = await db.get_messages(conv["id"], limit=20)
    if not messages:
        await update.message.reply_text("ℹ️ No messages in this conversation.")
        return

    lines = [f"📜 **History** (last {len(messages)} messages)\n"]

    for msg in messages:
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        content = truncate(msg["content"], 150)
        timestamp = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
        lines.append(f"{role_emoji} `{timestamp}` {content}")

    text = "\n".join(lines)

    # Truncate if too long
    if len(text) > 4096:
        text = text[:4090] + "\n..."

    await update.message.reply_text(text, parse_mode="Markdown")


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /clear — Delete all conversation history from the database.
    """
    user_id = update.effective_user.id
    db = context.bot_data.get("db")

    if not db:
        await update.message.reply_text("❌ Database not available.")
        return

    count = await db.clear_history(user_id)

    if count > 0:
        await update.message.reply_text(
            f"🗑 History cleared! ({count} conversation(s) deleted)"
        )
    else:
        await update.message.reply_text("ℹ️ No history to clear.")

    logger.info(f"User {user_id} cleared history ({count} conversations)")
