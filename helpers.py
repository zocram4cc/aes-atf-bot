import asyncio
import logging
import sys
import psutil
import vgamepad as vg
import yaml
from ocr import fuzzy_match, ocr_region

class SelectionState:
    def __init__(self):
        self.player_last_direction = 'DOWN'

def load_configs(teams_config_path, version):
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    if not version:
        logging.error("Version not provided.")
        sys.exit(1)
        
    version_config = config.get(version, {})
    
    with open(teams_config_path, 'r') as f:
        teams_config = yaml.safe_load(f)
        
    ocr_regions = version_config.get('ocr_regions', {})
    return config, teams_config, ocr_regions

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

async def select_league(obs, gamepad, ocr_reader, ocr_regions, config, leagues, target_league, state):
    logging.info(f"Starting league selection for '{target_league}'.")
    while True:
        await asyncio.sleep(1 / 10) # Read screen 10 times a second
        frame = obs.get_frame()
        if frame is None:
            continue

        p1_league_text = ocr_region(frame, 'p1_league_text', ocr_regions, ocr_reader)
        p1_current_league = fuzzy_match(p1_league_text, leagues, config)

        if p1_current_league is None:
            logging.warning(f"TEAM_SELECT: Could not match OCR text '{p1_league_text}'. Repeating last action: {state.player_last_direction}.")
            if state.player_last_direction == 'UP':
                await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2)
            else:
                await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2)
            continue

        if p1_current_league == target_league:
            logging.info(f"LEAGUE_SELECT: On target league '{target_league}'.")
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            break
        else:
            try:
                current_index = leagues.index(p1_current_league)
                target_index = leagues.index(target_league)
                if current_index < target_index:
                    logging.info(f"LEAGUE_SELECT: Current '{p1_current_league}' is before '{target_league}', pressing DOWN.")
                    state.player_last_direction = 'DOWN'
                    await self.press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2) # fix for Vigem windows users
                else:
                    logging.info(f"LEAGUE_SELECT: Current '{p1_current_league}' is after '{target_league}', pressing UP.")
                    state.player_last_direction = 'UP'
                    await self.press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2) # fix for Vigem windows users
            except ValueError:
                logging.error(f"League '{target_league}' or '{p1_current_league}' not in list. Skipping.")
                state.player_last_direction = 'DOWN'
                await self.press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2) # fix for Vigem windows users

async def select_team(obs, gamepad, ocr_reader, ocr_regions, config, all_teams, desired_team, state):
    logging.info(f"Starting team selection for '{desired_team}'.")
    desired_team_lower = desired_team.lower().strip('/')
    
    while True:
        await asyncio.sleep(1 / 10)
        frame = obs.get_frame()
        if frame is None:
            continue

        player1_text = ocr_region(frame, 'p1_team_select_text', ocr_regions, ocr_reader)
        
        processed_text = player1_text.lower()
        
        slash_like_chars = config.get('ocr_corrections', {}).get('slash_like_characters', [])
        if slash_like_chars and len(processed_text) > 1:
            if processed_text[0] in slash_like_chars:
                processed_text = '/' + processed_text[1:]
            if processed_text[-1] in slash_like_chars:
                processed_text = processed_text[:-1] + '/'
        
        if processed_text.startswith('/') and processed_text.endswith('/'):
            processed_text = processed_text[1:-1]
            
        current_team = fuzzy_match(processed_text, all_teams, config)

        if current_team is None:
            logging.warning(f"TEAM_SELECT: Could not match OCR text '{player1_text}'. Repeating last action: {state.player_last_direction}.")
            if state.player_last_direction == 'UP':
                await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2)
            else:
                await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2)
            continue
        
        logging.debug(f"TEAM_SELECT OCR: '{player1_text}' -> Matched: '{current_team}'")

        desired_team_name = desired_team.strip('/')
        if current_team.lower() == desired_team_name.lower():
            logging.info(f"TEAM_SELECT: Desired team '{desired_team}' found, pressing A.")
            await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            break
        else:
            try:
                current_index = all_teams.index(current_team)
                target_index = all_teams.index(desired_team_name)

                if current_index < target_index:
                    logging.info(f"TEAM_SELECT: Navigating DOWN for '{desired_team}'. Current: '{current_team}'.")
                    state.player_last_direction = 'DOWN'
                    await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2) # fix for Vigem windows users
                else: # current_index > target_index
                    logging.info(f"TEAM_SELECT: Navigating UP for '{desired_team}'. Current: '{current_team}'.")
                    state.player_last_direction = 'UP'
                    await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.2) # fix for Vigem windows users
            except ValueError:
                logging.error(f"Team '{desired_team_name}' or '{current_team}' not in list. Defaulting to DOWN.")
                state.player_last_direction = 'DOWN'
                await press_key(gamepad, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2) # fix for Vigem windows users