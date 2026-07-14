"""
Model management handlers — list, view, and switch models.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.config import get_available_models

logger = logging.getLogger(__name__)


async def models_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /models — List all available models with inline keyboard for quick selection.
    """
    agent_manager = context.bot_data["agent_manager"]
    session_info = agent_manager.get_session_info(update.effective_user.id)
    current_model = session_info["model"] if session_info else "default"

    available_models = get_available_models()
    lines = ["🤖 **Available models:**\n"]
    keyboard = []

    for model_id in available_models:
        marker = " ✅" if model_id == current_model else ""
        lines.append(f"• `{model_id}`{marker}")

        button_text = f"{'✅ ' if model_id == current_model else ''}{model_id}"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"model:{model_id}")]
        )

    lines.append(f"\n📌 Current model: `{current_model}`")

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /model [name] — View current model or switch to a new one.
    """
    agent_manager = context.bot_data["agent_manager"]
    user_id = update.effective_user.id

    # If no argument, show current model
    if not context.args:
        session_info = agent_manager.get_session_info(user_id)
        if session_info:
            await update.message.reply_text(
                f"🤖 Current model: `{session_info['model']}`\n\n"
                f"Use `/models` to see options or `/model <name>` to switch.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "ℹ️ No active session. Send a message to start one!",
            )
        return

    # Switch model
    model_name = " ".join(context.args)
    await _switch_model(update, context, user_id, model_name)


async def model_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard model selection."""
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("model:"):
        return

    model_name = query.data.split(":", 1)[1]
    user_id = update.effective_user.id

    await _switch_model(update, context, user_id, model_name, is_callback=True)


async def _switch_model(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    model_name: str,
    is_callback: bool = False,
):
    """Switch to a new model."""
    agent_manager = context.bot_data["agent_manager"]
    db = context.bot_data.get("db")

    available_models = get_available_models()

    # Validate model name
    if model_name not in available_models and model_name != "default":
        available = ", ".join(f"`{m}`" for m in available_models)
        text = (
            f"❌ Unknown model: `{model_name}`\n\n"
            f"Available models:\n{available}"
        )
        if is_callback:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
        return

    # Switch model (this restarts the session)
    result = await agent_manager.change_model(user_id, model_name)

    # Save preference
    if db:
        await db.set_preferred_model(user_id, model_name)

    if is_callback:
        await update.callback_query.edit_message_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text(result, parse_mode="Markdown")

    logger.info(f"User {user_id} switched to model: {model_name}")
