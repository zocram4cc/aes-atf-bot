#! /usr/bin/env python3
import os
import sys

from python.log_username_clean import username_clean_from_logs
from python.main import main as bot_main
from python.lib.utils import COLORS
from python.lib.utils.app_tools import app_title
from python.lib.utils.logging_tools import logger_init, logger_stop
from python.lib.utils.pausing import pause


def get_main_folder():

    # Get the path of the folder containing the script
    current_folder_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Go back one folder until the Engines folder is reached or the root is reached
    while os.path.basename(current_folder_path) != "Engines":
        parent_folder_path = os.path.dirname(current_folder_path)
        if parent_folder_path == current_folder_path:
            # If the root is reached, show a fatal error and exit to avoid an infinite loop
            print( "-")
            print(f"- {COLORS.DARK_RED}FATAL ERROR{COLORS.RESET} - Wrong script location")
            print( "-")
            print( "- Please grab a clean compiler folder")
            print( "-")

            pause("Press any key to exit... ")
            sys.exit()

        current_folder_path = parent_folder_path

    # Return the folder containing the Engines folder
    return os.path.dirname(current_folder_path)

def main():

    # Set the working folder to the main compiler folder
    os.chdir(get_main_folder())

    # Run the bot
    bot_main()

    # Stop the loggers
    logger_stop()

    print("-")
    print("- Done")
    print("-")

    pause("Press any key to exit... ", print_hyphen=False)


if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "-1":
        # Run the log cleaner to remove the username from the logs
        username_clean_from_logs()
        sys.exit()

    if sys.platform == "win32":

        # Set the console title
        os.system("title " + app_title(colorize=False))

    print("-")
    print("-")
    print("- " + app_title())
    print("-")
    print("-")

    # Enable the advanced traceback handler
    from rich.traceback import install
    install(show_locals=True)

    # Enable the loggers
    logger_init()

    # Run the main function
    main()
