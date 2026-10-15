import os
import sys


if sys.platform == "win32":

    # Enable color on Windows 10+ only
    win_version = sys.getwindowsversion().major

    # Check if the NO_COLOR environment variable is set
    COLORIZE = "NO_COLOR" not in os.environ and win_version >= 10

    if COLORIZE:
        os.system("color")

else:
    # Check if the NO_COLOR environment variable is set
    COLORIZE = "NO_COLOR" not in os.environ

BLACK          = '\033[30m' if COLORIZE else ''

DARK_RED       = '\033[31m' if COLORIZE else ''
DARK_GREEN     = '\033[32m' if COLORIZE else ''
DARK_YELLOW    = '\033[33m' if COLORIZE else ''
DARK_BLUE      = '\033[34m' if COLORIZE else ''
DARK_MAGENTA   = '\033[35m' if COLORIZE else ''
DARK_CYAN      = '\033[36m' if COLORIZE else ''
DARK_WHITE     = '\033[37m' if COLORIZE else ''

BRIGHT_BLACK   = '\033[90m' if COLORIZE else ''
BRIGHT_RED     = '\033[91m' if COLORIZE else ''
BRIGHT_GREEN   = '\033[92m' if COLORIZE else ''
BRIGHT_YELLOW  = '\033[93m' if COLORIZE else ''
BRIGHT_BLUE    = '\033[94m' if COLORIZE else ''
BRIGHT_MAGENTA = '\033[95m' if COLORIZE else ''
BRIGHT_CYAN    = '\033[96m' if COLORIZE else ''
WHITE          = '\033[97m' if COLORIZE else ''

RESET          = '\033[0m' if COLORIZE else ''
