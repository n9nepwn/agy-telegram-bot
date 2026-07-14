"""
/start and /help command handlers.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = """
🤖 **AGY Telegram Bot**

Salut ! Je suis ton bridge vers **Antigravity** (AGY).
Envoie-moi un message et je le transmettrai à AGY.

**Commandes disponibles :**

💬 **Chat**
• Envoie un message texte → je le forward à AGY
• `/new` — Nouvelle conversation (reset le contexte)

🤖 **Modèles**
• `/model` — Voir le modèle actuel
• `/models` — Lister les modèles disponibles
• `/model <nom>` — Changer de modèle

📊 **Stats**
• `/quota` — Statistiques d'utilisation
• `/status` — État du bot et de la session

🔧 **Gestion**
• `/history` — Derniers messages de la session
• `/clear` — Effacer tout l'historique
• `/restart` — Redémarrer la session AGY

💡 _Powered by Google Antigravity SDK_
"""

HELP_MESSAGE = WELCOME_MESSAGE


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user
    logger.info(f"/start from {user.full_name} (id={user.id})")

    # Upsert user in database
    db = context.bot_data.get("db")
    if db:
        await db.upsert_user(user.id, user.username or "")

    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    await update.message.reply_text(
        HELP_MESSAGE,
        parse_mode="Markdown",
    )
