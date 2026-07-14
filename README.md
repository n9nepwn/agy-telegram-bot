# 🤖 AGY Telegram Bot

> Bridge entre **Telegram** et **Google Antigravity** (AGY) — discute avec AGY depuis ton téléphone.

## 🚀 Features

- 💬 **Chat avec AGY** directement depuis Telegram
- 🔄 **Streaming** — les réponses s'affichent progressivement
- 🤖 **Multi-modèles** — switch entre Gemini, Claude, etc.
- 📊 **Stats & quotas** — suivi de ta consommation
- 🗂 **Historique** — conversations persistées en SQLite
- 🔐 **Whitelist** — seuls les User IDs autorisés ont accès
- ♻️ **Sessions** — contexte indépendant par utilisateur

## 📋 Prérequis

- Python 3.11+
- Un compte Google avec AGY (plan Google AI Pro recommandé)
- AGY CLI installé et authentifié sur la machine (`gcloud auth` ou session AGY active)
- Un bot Telegram créé via [@BotFather](https://t.me/BotFather)

## 🛠 Installation

```bash
# Cloner le repo
git clone <your-repo-url>
cd agy-telegram-bot

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer
cp .env.example .env
nano .env  # Remplir TELEGRAM_BOT_TOKEN et ALLOWED_USER_IDS
```

### Configuration (.env)

| Variable | Description | Requis |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token du bot (via @BotFather) | ✅ |
| `ALLOWED_USER_IDS` | IDs Telegram autorisés (comma-separated) | ✅ |
| `DEFAULT_MODEL` | Modèle par défaut | ❌ |
| `LOG_LEVEL` | Niveau de log (DEBUG/INFO/WARNING/ERROR) | ❌ |
| `ENABLE_STREAMING` | Réponses en streaming (true/false) | ❌ |
| `SESSION_TIMEOUT_MINUTES` | Timeout d'inactivité des sessions | ❌ |
| `MAX_CONTEXT_MESSAGES` | Messages max en contexte | ❌ |

> 💡 **Trouver ton Telegram User ID** : envoie un message à [@userinfobot](https://t.me/userinfobot)

## 🏃 Lancement

```bash
# Directement
python -m bot.main

# Ou avec le module
python bot/main.py
```

## 📱 Commandes du Bot

| Commande | Description |
|---|---|
| `/start` | Message de bienvenue |
| `/help` | Aide et liste des commandes |
| `/new` | Nouvelle conversation (reset le contexte) |
| `/model` | Voir le modèle actuel |
| `/model <nom>` | Changer de modèle |
| `/models` | Lister les modèles avec boutons de sélection |
| `/quota` | Statistiques d'utilisation |
| `/history` | Derniers messages de la conversation |
| `/clear` | Effacer tout l'historique |
| `/status` | État du bot (uptime, sessions) |
| `/restart` | Redémarrer la session AGY |
| *(message)* | Chat direct avec AGY |

## 🏗 Architecture

```
agy-telegram-bot/
├── .env                  # Configuration (non versionné)
├── .env.example          # Template
├── requirements.txt      # Dépendances Python
├── bot/
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── agent.py          # Wrapper AGY SDK
│   ├── handlers/
│   │   ├── start.py      # /start, /help
│   │   ├── chat.py       # Messages texte → AGY
│   │   ├── models.py     # /model, /models
│   │   ├── session.py    # /new, /history, /clear
│   │   ├── quota.py      # /quota
│   │   └── admin.py      # /status, /restart
│   ├── middleware/
│   │   └── auth.py       # Whitelist auth
│   ├── database/
│   │   └── db.py         # SQLite persistence
│   └── utils/
│       └── formatting.py # Markdown & formatting
├── Dockerfile
└── README.md
```

## 🐳 Docker

```bash
# Build
docker build -t agy-telegram-bot .

# Run
docker run -d \
  --name agy-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  agy-telegram-bot
```

## 📝 Notes

- **Quotas** : Le SDK utilise les mêmes quotas que AGY CLI/Desktop (plan Google AI Pro)
- **Modèles** : Pas besoin de `vertex=True`, le mode par défaut utilise ton compte Google personnel
- **Sécurité** : Ne partage JAMAIS ton `.env` — il contient ton bot token
- **Sessions** : Chaque user a sa propre session AGY avec contexte indépendant
- **Timeout** : Les sessions inactives sont automatiquement nettoyées

## 📄 License

MIT
