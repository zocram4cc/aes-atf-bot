import os
import sys
import logging

from rich.console import Console
from rich.traceback import Traceback

from . import COLORS
from .pausing import pause
from .app_tools import app_title
from .FILE_INFO import (
    SUGGESTIONS_LOG_PATH,
    ISSUES_LOG_PATH,
    CRASH_LOG_PATH
)


class ColorFilter(logging.Filter):
    """
    This is a filter which colorizes the alert words "FATAL", "ERROR" and "Warning".
    """

    def filter(self, record):

        FATAL_STRING = "FATAL"
        FATAL_STRING_COLORED = COLORS.DARK_RED + "FATAL" + COLORS.RESET
        record.msg = record.msg.replace(FATAL_STRING, FATAL_STRING_COLORED)

        ERROR_STRING = "ERROR"
        ERROR_STRING_COLORED = COLORS.DARK_RED + "ERROR" + COLORS.RESET
        record.msg = record.msg.replace(ERROR_STRING, ERROR_STRING_COLORED)

        WARNING_STRING = "Warning"
        WARNING_STRING_COLORED = COLORS.DARK_YELLOW + "Warning" + COLORS.RESET
        record.msg = record.msg.replace(WARNING_STRING, WARNING_STRING_COLORED)

        return True


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler that logs unhandled exceptions directly to files with Rich formatting
    while still displaying rich tracebacks on console.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow normal handling of KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # First, display the Rich traceback on console (this is what the user sees)
    console = Console(stderr=True)
    traceback_obj = Traceback.from_exception(
        exc_type, exc_value, exc_traceback,
        show_locals=True,
        locals_max_length=None,
        suppress=[],
        max_frames=50
    )
    console.print(traceback_obj)

    # Create console for file output (no color codes, no fancy characters)
    file_console = Console(
        file=None, width=120, legacy_windows=False, force_terminal=False,
        no_color=True, safe_box=True
    )

    # Write to crash.log
    try:
        with open(CRASH_LOG_PATH, 'a', encoding='utf-8') as crash_file:
            crash_file.write("\nUNHANDLED EXCEPTION:\n")
            file_console.file = crash_file
            file_console.print(traceback_obj)
            file_console.file = None
    except Exception:
        pass  # Don't let logging errors crash the program

    # Write to issues.log
    try:
        with open(ISSUES_LOG_PATH, 'a', encoding='utf-8') as issues_file:
            issues_file.write("\nUNHANDLED EXCEPTION:\n")
            file_console.file = issues_file
            file_console.print(traceback_obj)
            file_console.file = None
    except Exception:
        pass  # Don't let logging errors crash the program


def log_store(log_path):

    if not os.path.exists(log_path):
        return

    log_path_splitext = os.path.splitext(log_path)
    log_path_old = log_path_splitext[0] + ".old" + log_path_splitext[1]

    log_name = os.path.basename(log_path)

    if os.path.exists(log_path_old):
        os.remove(log_path_old)

    try:
        os.rename(log_path, log_path_old)

    except PermissionError:
        print( "-")
        print(f"- {COLORS.DARK_RED}FATAL ERROR{COLORS.RESET} - Error while trying to rename the {log_name} file")
        print( "- Please check if it's open in another program, or")
        print( "- if you have left another session of the compiler open")

        print( "-")
        input("Press Enter to continue after checking... ")

        try:
            os.rename(log_path, log_path_old)

        except PermissionError:
            print( "-")
            print(f"- {COLORS.DARK_RED}FATAL ERROR{COLORS.RESET} - Cannot rename the {log_name} file")
            print( "- Restart your PC and try again")

            pause("Press any key to exit... ", force=True)

            sys.exit()


def logger_init():

    # Set the root logger level
    logging.getLogger().setLevel(logging.INFO)


    # If a suggestions log file already exists, add .old to it
    log_store(SUGGESTIONS_LOG_PATH)

    # Create a file handler which will only store INFO messages
    # It will only create a file when a message occurs
    suggestions_log_handler = logging.FileHandler(SUGGESTIONS_LOG_PATH, delay=True, encoding="utf-8")
    suggestions_log_handler.setLevel(logging.INFO)
    suggestions_log_handler.addFilter(lambda record: record.levelno == logging.INFO)

    # Add it to the root logger
    logging.getLogger().addHandler(suggestions_log_handler)


    # If an issues log file already exists, add .old to it
    log_store(ISSUES_LOG_PATH)

    # Create a file handler which which will only store WARNING messages or higher
    # It will only create a file when a message occurs
    issues_log_handler = logging.FileHandler(ISSUES_LOG_PATH, delay=True, encoding="utf-8")
    issues_log_handler.setLevel(logging.WARNING)

    # Add it to the root logger
    logging.getLogger().addHandler(issues_log_handler)


    # Create a stream handler for outputting colored errors to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.addFilter(ColorFilter())

    # Add it to the root logger
    logging.getLogger().addHandler(stream_handler)


    # If a crash log file already exists, add .old to it
    log_store(CRASH_LOG_PATH)

    # Install the global exception handler to capture unhandled exceptions
    sys.excepthook = global_exception_handler


def logger_stop():

    logging.shutdown()

    # Check if any of the non-crash log files exist and add the program version to them
    for log_path in [SUGGESTIONS_LOG_PATH, ISSUES_LOG_PATH]:
        if os.path.isfile(log_path):
            with open(log_path, "r", encoding="utf-8") as log_file:
                previous_contents = log_file.read()

            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write("- " + app_title(colorize=False) + "\n" + previous_contents)


def log_presence_warn():

    issues_log_present = os.path.exists(ISSUES_LOG_PATH)
    suggestions_log_present = os.path.exists(SUGGESTIONS_LOG_PATH)

    if issues_log_present:
        # Warn about there being some issues and about having to open the log
        print( "-")
        print(f"- {COLORS.DARK_YELLOW}Warning{COLORS.RESET}: There were some potential issues in the exports")
        print( "- Please check the issues.log file for more details")
    else:
        print( "-")
        print(f"- {COLORS.DARK_GREEN}No issues were found{COLORS.RESET}")

    if suggestions_log_present:
        # Warn about there being some suggestions
        print( "-")
        print(f"- {COLORS.DARK_CYAN}Info{COLORS.RESET}: There are some suggestions available")
        print( "- Check the suggestions.log file to improve your aesthetics")

    return issues_log_present
