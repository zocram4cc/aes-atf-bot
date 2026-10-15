from . import COLORS
from .APP_DATA import (
    APP_VERSION_MAJOR,
    APP_VERSION_MINOR,
    APP_VERSION_PATCH,
    APP_VERSION_DEV,
)


def app_title(colorize=True):

    color_bright_cyan = COLORS.BRIGHT_CYAN if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    version_string = f"{APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}"
    dev_string = f"-{color_bright_cyan}dev{color_reset}" if APP_VERSION_DEV else ""

    title_string = f"4cc aes bot {version_string}{dev_string}"

    return title_string


def pes_title(pes_version, colorize=True):

    color_dark_cyan = COLORS.DARK_CYAN if colorize else ""
    color_bright_red = COLORS.BRIGHT_RED if colorize else ""
    color_bright_green = COLORS.BRIGHT_GREEN if colorize else ""
    color_bright_yellow = COLORS.BRIGHT_YELLOW if colorize else ""
    color_bright_blue = COLORS.BRIGHT_BLUE if colorize else ""
    color_bright_magenta = COLORS.BRIGHT_MAGENTA if colorize else ""
    color_bright_cyan = COLORS.BRIGHT_CYAN if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    match int(pes_version):
        case 15:
            pes_color = color_dark_cyan
        case 16:
            pes_color = color_bright_magenta
        case 17:
            pes_color = color_bright_yellow
        case 18:
            pes_color = color_bright_cyan
        case 19:
            pes_color = color_bright_blue
        case 21:
            pes_color = color_bright_green
        case _:
            pes_color = color_bright_red

    title_string = f"{pes_color}PES20{pes_version}{color_reset}"

    return title_string
