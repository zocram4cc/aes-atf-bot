import os

from .lib.utils.FILE_INFO import (
    ISSUES_LOG_PATH,
    CRASH_LOG_PATH
)


def username_clean_from_log(log_path):

    if not os.path.exists(log_path):
        return

    username = os.getenv("USERNAME", "unknown")

    with open(log_path, "r", encoding='utf-8') as f:
        text = f.readlines()

    username_length = len(username)

    if username_length > 10:
        prefix_length = (username_length - 10) // 2
        suffix_length = (username_length - 10) - prefix_length
        dummy_name = " "*prefix_length + "<username>" + " "*suffix_length
    else:
        dummy_name = "<username"[:username_length-1] + ">"

    text = [line.replace(f"\\{username}\\", f"\\{dummy_name}\\") for line in text]

    with open(log_path, "w", encoding='utf-8') as f:
        f.writelines(text)

def username_clean_from_logs():
    username_clean_from_log(ISSUES_LOG_PATH)
    username_clean_from_log(CRASH_LOG_PATH)


if __name__ == "__main__":

    username_clean_from_logs()
