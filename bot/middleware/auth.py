"""
Auth middleware — restricts bot access to whitelisted Telegram User IDs.
"""

import logging
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def require_auth(allowed_user_ids: list[int]):
    """
    Decorator that restricts handler access to whitelisted users.

    Usage:
        @require_auth(settings.allowed_user_ids)
        async def my_handler(update, context):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            if not user:
                return

            if user.id not in allowed_user_ids:
                logger.warning(
                    f"🚫 Unauthorized access attempt: "
                    f"user_id={user.id}, username=@{user.username}, "
                    f"name={user.full_name}"
                )
                await update.message.reply_text(
                    "🔒 Accès refusé.\n\n"
                    "Ce bot est privé. Si tu penses que c'est une erreur, "
                    "contacte l'administrateur."
                )
                return

            return await func(update, context)

        return wrapper

    return decorator


def require_auth_callback(allowed_user_ids: list[int]):
    """
    Same as require_auth but for callback query handlers.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            if not user or user.id not in allowed_user_ids:
                if update.callback_query:
                    await update.callback_query.answer(
                        "🔒 Accès refusé.", show_alert=True
                    )
                return

            return await func(update, context)

        return wrapper

    return decorator
