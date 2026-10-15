import asyncio
import logging
import sys
import psutil
import vgamepad as vg
import yaml

class SelectionState:
    def __init__(self):
        self.current_league_index = 0
        self.current_team_index = 0

def load_configs(teams_config_path, version):
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    if not version:
        logging.error("Version not provided.")
        sys.exit(1)

    with open(teams_config_path, 'r') as f:
        teams_config = yaml.safe_load(f)

    return config, teams_config

def check_process_running(process_name_pattern):
    for proc in psutil.process_iter(['name']):
        if process_name_pattern in proc.info['name']:
            return True
    return False

async def press_key(gamepad, button, sleep_time=0.2):
    gamepad.press_button(button=button)
    gamepad.update()
    await asyncio.sleep(sleep_time)
    gamepad.release_button(button=button)
    gamepad.update()
    await asyncio.sleep(0.1)

async def press_left_analog(gamepad, direction, sleep_time=0.2):
    if direction == 'UP':
        y_val = -1.0
    elif direction == 'DOWN':
        y_val = 1.0
    else:
        y_val = 0.0

    if direction == 'LEFT':
        x_val = -1.0
    elif direction == 'RIGHT':
        x_val = 1.0
    else:
        x_val = 0.0
    gamepad.left_joystick_float(x_value_float=x_val, y_value_float=y_val)
    gamepad.update()
    await asyncio.sleep(sleep_time)
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    gamepad.update()
    await asyncio.sleep(0.1)

async def select_league(gamepad, target_index, state):
    logging.info(f"Starting league selection for index {target_index} (current: {state.current_league_index}).")
    diff = target_index - state.current_league_index

    if diff > 0:
        logging.info(f"LEAGUE_SELECT: Navigating DOWN {diff} times from index {state.current_league_index} to {target_index}.")
        for _ in range(diff):
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2)
            await asyncio.sleep(0.3)
    elif diff < 0:
        logging.info(f"LEAGUE_SELECT: Navigating UP {-diff} times from index {state.current_league_index} to {target_index}.")
        for _ in range(-diff):
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2)
            await asyncio.sleep(0.3)
    else:
        logging.info(f"LEAGUE_SELECT: Already on target index {target_index}.")

    state.current_league_index = target_index
    await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

async def select_team(gamepad, target_index, state):
    logging.info(f"Starting team selection for index {target_index} (current: {state.current_team_index}).")
    diff = target_index - state.current_team_index

    if diff > 0:
        logging.info(f"TEAM_SELECT: Navigating DOWN {diff} times from index {state.current_team_index} to {target_index}.")
        for _ in range(diff):
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2)
            await asyncio.sleep(0.3)
    elif diff < 0:
        logging.info(f"TEAM_SELECT: Navigating UP {-diff} times from index {state.current_team_index} to {target_index}.")
        for _ in range(-diff):
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2)
            await asyncio.sleep(0.3)
    else:
        logging.info(f"TEAM_SELECT: Already on target index {target_index}.")

    state.current_team_index = target_index
    await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)