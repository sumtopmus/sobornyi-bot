from telegram import User


def replace_brackets(text: str) -> str:
    """Replace brackets in the text with parentheses."""
    return text.replace(r"[", r"(").replace(r"]", r")")


def mention(user: User) -> str:
    """Create a user's mention."""
    result = user.mention_markdown(user.name)
    if user.username:
        result += f" ({user.mention_markdown()})"
    return result
