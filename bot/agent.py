"""
AGY Agent Wrapper — manages Antigravity agent sessions per Telegram user.

Each user gets their own Agent instance with independent conversation context.
Sessions are automatically cleaned up after inactivity timeout.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field

from google.antigravity import Agent, LocalAgentConfig

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Tracks an active AGY session for a single Telegram user."""

    user_id: int
    agent: Agent
    model: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    is_busy: bool = False

    def touch(self):
        """Update last active timestamp."""
        self.last_active = time.time()


class AGYSessionManager:
    """
    Manages AGY agent sessions for multiple Telegram users.

    Each user gets their own Agent instance. Sessions are created on demand
    and cleaned up after a configurable inactivity timeout.
    """

    def __init__(self, default_model: str = "", session_timeout_minutes: int = 60):
        self._sessions: dict[int, UserSession] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._default_model = default_model
        self._session_timeout = session_timeout_minutes * 60  # Convert to seconds
        self._cleanup_task: asyncio.Task | None = None

    async def start(self):
        """Start the session manager and background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("AGY Session Manager started")

    async def stop(self):
        """Stop the session manager and close all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all active sessions
        for user_id in list(self._sessions.keys()):
            await self.destroy_session(user_id)

        logger.info("AGY Session Manager stopped — all sessions closed")

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific user."""
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def get_or_create_session(self, user_id: int, model: str = "") -> UserSession:
        """
        Get an existing session or create a new one for the user.

        Args:
            user_id: Telegram user ID.
            model: Model to use. Falls back to user's last model or default.

        Returns:
            The user's active session.
        """
        lock = self._get_lock(user_id)
        async with lock:
            if user_id in self._sessions:
                session = self._sessions[user_id]
                session.touch()
                return session

            # Create a new session
            return await self._create_session(user_id, model or self._default_model)

    async def _create_session(self, user_id: int, model: str = "") -> UserSession:
        """Create a new AGY agent session for a user."""
        logger.info(f"Creating new AGY session for user {user_id} (model: {model or 'default'})")

        config = LocalAgentConfig()

        agent = Agent(config)
        await agent.__aenter__()

        session = UserSession(
            user_id=user_id,
            agent=agent,
            model=model or "default",
        )

        self._sessions[user_id] = session
        logger.info(f"Session created for user {user_id}")
        return session

    async def chat(self, user_id: int, message: str) -> str:
        """
        Send a message to AGY and get the response.

        Args:
            user_id: Telegram user ID.
            message: The user's message.

        Returns:
            AGY's response text.
        """
        session = await self.get_or_create_session(user_id)

        if session.is_busy:
            return "⏳ Je suis encore en train de traiter ta dernière requête, patiente un instant..."

        session.is_busy = True
        try:
            response = await session.agent.chat(message)
            text = await response.text()

            # Update session stats
            session.message_count += 1
            session.touch()

            # Try to get token usage if available
            try:
                if hasattr(response, 'usage'):
                    usage = response.usage
                    if hasattr(usage, 'input_tokens'):
                        session.total_input_tokens += usage.input_tokens
                    if hasattr(usage, 'output_tokens'):
                        session.total_output_tokens += usage.output_tokens
            except Exception:
                pass  # Token tracking is best-effort

            return text

        except Exception as e:
            logger.error(f"AGY chat error for user {user_id}: {e}", exc_info=True)
            return f"❌ Erreur AGY : {str(e)}"
        finally:
            session.is_busy = False

    async def chat_stream(self, user_id: int, message: str):
        """
        Send a message to AGY and yield response chunks as they arrive.

        Args:
            user_id: Telegram user ID.
            message: The user's message.

        Yields:
            String chunks of the response.
        """
        session = await self.get_or_create_session(user_id)

        if session.is_busy:
            yield "⏳ Je suis encore en train de traiter ta dernière requête, patiente un instant..."
            return

        session.is_busy = True
        try:
            response = await session.agent.chat(message)

            # Try streaming first
            full_text = ""
            try:
                async for chunk in response:
                    full_text += chunk
                    yield chunk
            except (TypeError, AttributeError):
                # Fallback to non-streaming if streaming isn't supported
                text = await response.text()
                yield text
                full_text = text

            session.message_count += 1
            session.touch()

        except Exception as e:
            logger.error(f"AGY stream error for user {user_id}: {e}", exc_info=True)
            yield f"❌ Erreur AGY : {str(e)}"
        finally:
            session.is_busy = False

    async def new_session(self, user_id: int, model: str = "") -> str:
        """
        Destroy the current session and create a new one (fresh context).

        Args:
            user_id: Telegram user ID.
            model: Optional model override for the new session.

        Returns:
            Confirmation message.
        """
        old_model = ""
        if user_id in self._sessions:
            old_model = self._sessions[user_id].model
            await self.destroy_session(user_id)

        use_model = model or old_model
        await self.get_or_create_session(user_id, use_model)
        return f"🔄 Nouvelle session créée ! (modèle : {use_model or 'default'})"

    async def change_model(self, user_id: int, model: str) -> str:
        """
        Change the model for a user's session (requires session restart).

        Args:
            user_id: Telegram user ID.
            model: The new model name.

        Returns:
            Confirmation message.
        """
        if user_id in self._sessions and self._sessions[user_id].is_busy:
            return "⏳ Impossible de changer de modèle pendant un traitement en cours."

        await self.destroy_session(user_id)
        await self.get_or_create_session(user_id, model)
        return f"✅ Modèle changé : **{model}**\nNouvelle session démarrée."

    async def destroy_session(self, user_id: int):
        """Close and remove a user's session."""
        if user_id in self._sessions:
            session = self._sessions[user_id]
            try:
                await session.agent.__aexit__(None, None, None)
                logger.info(f"Session closed for user {user_id}")
            except Exception as e:
                logger.error(f"Error closing session for user {user_id}: {e}")
            finally:
                del self._sessions[user_id]

    def get_session_info(self, user_id: int) -> dict | None:
        """Get info about a user's current session."""
        if user_id not in self._sessions:
            return None

        session = self._sessions[user_id]
        uptime = time.time() - session.created_at
        idle = time.time() - session.last_active

        return {
            "model": session.model,
            "message_count": session.message_count,
            "uptime_minutes": round(uptime / 60, 1),
            "idle_minutes": round(idle / 60, 1),
            "total_input_tokens": session.total_input_tokens,
            "total_output_tokens": session.total_output_tokens,
            "is_busy": session.is_busy,
        }

    def get_all_sessions_info(self) -> dict:
        """Get summary info about all active sessions."""
        return {
            "active_sessions": len(self._sessions),
            "sessions": {
                uid: self.get_session_info(uid) for uid in self._sessions
            },
        }

    async def _cleanup_loop(self):
        """Periodically clean up inactive sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                now = time.time()
                expired = [
                    uid
                    for uid, session in self._sessions.items()
                    if (now - session.last_active) > self._session_timeout
                    and not session.is_busy
                ]
                for uid in expired:
                    logger.info(f"Cleaning up inactive session for user {uid}")
                    await self.destroy_session(uid)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
