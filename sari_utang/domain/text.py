"""Cleaning typed text and search text."""


def clean_text(value):
    """One line: trimmed, with runs of spaces made single ("  Aling   Nena " -> "Aling Nena")."""
    return " ".join(str(value or "").split())


def like_pattern(text):
    """Search text -> a LIKE pattern that finds it anywhere ("coke" -> "%coke%").

    In LIKE, % and _ are wildcards; they are escaped so searching "50%" finds "50%".
    Use with: ... LIKE ? ESCAPE '\\'
    """
    text = clean_text(text)
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
