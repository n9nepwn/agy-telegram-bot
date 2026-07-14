"""
Formatting utilities — convert between AGY markdown and Telegram MarkdownV2.
"""

import re

# Characters that must be escaped in Telegram MarkdownV2
_ESCAPE_CHARS = r"_[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 format.

    Preserves existing markdown formatting (bold, italic, code blocks).
    """
    # Process code blocks first (don't escape inside them)
    parts = []
    last_end = 0

    # Handle ``` code blocks
    for match in re.finditer(r"```[\s\S]*?```", text):
        # Escape text before this code block
        before = text[last_end : match.start()]
        parts.append(_escape_text(before))
        # Keep code block as-is (Telegram handles it)
        parts.append(match.group())
        last_end = match.end()

    # Handle inline `code`
    remaining = text[last_end:]
    inline_parts = []
    inline_last = 0
    for match in re.finditer(r"`[^`]+`", remaining):
        before = remaining[inline_last : match.start()]
        inline_parts.append(_escape_text(before))
        inline_parts.append(match.group())
        inline_last = match.end()

    inline_parts.append(_escape_text(remaining[inline_last:]))
    parts.append("".join(inline_parts))

    return "".join(parts)


def _escape_text(text: str) -> str:
    """Escape special chars in plain text (outside code blocks)."""
    for char in _ESCAPE_CHARS:
        text = text.replace(char, f"\\{char}")
    return text


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Split a long message into chunks that fit Telegram's message limit.

    Tries to split at natural boundaries (newlines, sentences) rather
    than mid-word.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Try to split at a newline
        split_at = text.rfind("\n", 0, max_length)

        # If no newline, try a period
        if split_at == -1:
            split_at = text.rfind(". ", 0, max_length)
            if split_at != -1:
                split_at += 1  # Include the period

        # If no period, try a space
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_length)

        # Last resort: hard cut
        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks


def format_code_block(code: str, language: str = "") -> str:
    """Format a code block for Telegram."""
    return f"```{language}\n{code}\n```"


def format_session_info(info: dict) -> str:
    """Format session info dict into a readable Telegram message."""
    if not info:
        return "ℹ️ No active session."

    lines = [
        "📊 **Session Info**\n",
        f"🤖 Model: `{info['model']}`",
        f"💬 Messages: {info['message_count']}",
        f"⏱ Uptime: {info['uptime_minutes']} min",
        f"😴 Idle: {info['idle_minutes']} min",
    ]

    if info.get("total_input_tokens") or info.get("total_output_tokens"):
        lines.append(f"📥 Tokens in: {info['total_input_tokens']:,}")
        lines.append(f"📤 Tokens out: {info['total_output_tokens']:,}")

    if info.get("is_busy"):
        lines.append("\n⏳ **Processing...**")

    return "\n".join(lines)


def format_usage_stats(stats: dict) -> str:
    """Format usage stats into a readable Telegram message."""
    return "\n".join([
        "📊 **Usage Statistics**\n",
        f"💬 Messages today: {stats.get('messages_24h', 0)}",
        f"📅 Messages this week: {stats.get('messages_7d', 0)}",
        f"📆 Messages this month: {stats.get('messages_30d', 0)}",
        f"📝 Total messages: {stats.get('total_messages', 0)}",
        f"🗂 Total conversations: {stats.get('total_conversations', 0)}",
        f"🔢 Total tokens: {stats.get('total_tokens', 0):,}",
    ])


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
