"""Cross-platform terminal color support."""

import os
import sys


_enabled = True


def init(*, no_color=False):
    """Initialize color support.

    Colors are disabled if:
    - no_color is True (--no-color flag)
    - NO_COLOR environment variable is set
    - stdout is not a TTY
    """
    global _enabled
    _enabled = not no_color and "NO_COLOR" not in os.environ and sys.stdout.isatty()

    # Enable ANSI colors on Windows
    if _enabled and sys.platform == "win32":
        os.system("")  # noqa: S605


def _wrap(code, text):
    if _enabled:
        return f"\033[{code}m{text}\033[0m"
    return text


def bold(text):
    return _wrap("1", text)


def dim(text):
    return _wrap("2", text)


def green(text):
    return _wrap("32", text)


def yellow(text):
    return _wrap("33", text)


def blue(text):
    return _wrap("34", text)


def cyan(text):
    return _wrap("36", text)


def red(text):
    return _wrap("31", text)
