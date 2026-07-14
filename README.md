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
- 🔧 **CLI complète** — `agy-telegram-bot` pour tout gérer depuis le terminal

## 📋 Prérequis

- Python 3.11+
- Un compte Google avec AGY (plan Google AI Pro recommandé)
- AGY CLI installé et authentifié sur la machine (`gcloud auth` ou session AGY active)
- Un bot Telegram créé via [@BotFather](https://t.me/BotFather)

## ⚡ Quick Start (3 commandes)

```bash
git clone <your-repo-url> && cd agy-telegram-bot
./install.sh
agy-telegram-bot start
```

L'installeur fait tout automatiquement :
1. ✅ Crée le virtual environment
2. ✅ Installe les dépendances
3. ✅ Enregistre la commande `agy-telegram-bot` globalement
4. ✅ Lance le wizard de configuration

## 🔧 CLI — Commandes Terminal

```
agy-telegram-bot setup               Configure le bot (token, users, modèle)
agy-telegram-bot start               Démarre le bot en arrière-plan
agy-telegram-bot stop                Arrête le bot
agy-telegram-bot restart             Redémarre le bot
agy-telegram-bot status              État du bot (PID, uptime, mémoire, config)
agy-telegram-bot logs                Logs en direct (Ctrl+C pour arrêter)
agy-telegram-bot logs -n 50          Dernières 50 lignes de logs
agy-telegram-bot logs --clear        Vide le fichier de logs
agy-telegram-bot auth                Liste les utilisateurs autorisés
agy-telegram-bot auth add <ID>       Autorise un utilisateur Telegram
agy-telegram-bot auth remove <ID>    Retire un utilisateur
agy-telegram-bot auth test           Teste la configuration (token, SDK, auth)
```

## 📱 Commandes Telegram

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

## ⚙️ Configuration

Le wizard `agy-telegram-bot setup` configure tout interactivement. Sinon, édite `.env` :

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

## 🏗 Architecture

```
agy-telegram-bot/
├── install.sh            # Installeur one-line
├── uninstall.sh          # Désinstalleur propre
├── pyproject.toml        # Config projet + entry point CLI
├── requirements.txt      # Dépendances Python
├── Dockerfile            # Image Docker
├── bot/
│   ├── main.py           # Entry point du bot
│   ├── cli.py            # CLI terminal (agy-telegram-bot)
│   ├── daemon.py         # Gestion du daemon (PID, start/stop)
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
└── README.md
```

## 🐳 Docker

```bash
docker build -t agy-telegram-bot .
docker run -d --name agy-bot --env-file .env -v $(pwd)/data:/app/data agy-telegram-bot
```

## 🗑 Désinstallation

```bash
./uninstall.sh
```

## 📝 Notes

- **Quotas** : Le SDK utilise les mêmes quotas que AGY CLI/Desktop (plan Google AI Pro à ~20€)
- **Pas de `vertex=True`** : le mode par défaut utilise ton compte Google personnel
- **Sécurité** : Ne partage JAMAIS ton `.env` — il contient ton bot token
- **Sessions** : Chaque user a sa propre session AGY avec contexte indépendant
- **Auto-cleanup** : Les sessions inactives sont automatiquement fermées

## 📄 License

MIT
