import os
import sys


def pause(message="Press any key to continue... ", print_hyphen=True, force=False):
    """
    Pauses the program and waits for Enter.

    Args:
        message (str, optional): The message to be displayed before waiting for the user to press a key. Defaults to "Press any key to continue... ".

    Returns:
        None
    """
    pause_allow = os.environ.get('PAUSE_ALLOW', '1')
    if pause_allow == '0' and not force:
        return

    if print_hyphen:
        print("-")

    print(message, end='', flush=True)

    if sys.platform == 'win32':
        os.system('pause >nul')
        print("")

    else:
        os.system("read -n1 -r")
