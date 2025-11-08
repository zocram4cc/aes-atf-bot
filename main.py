
import asyncio
import logging
import os
import platform
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import easyocr
import numpy as np
import psutil
import vgamepad as vg
import yaml
from obswebsocket import requests as obs_requests
from screen_capture import OBSClient

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global Variables ---
CONFIG = None
TEAMS_CONFIG = None
OCR_READER = None
OCR_REGIONS = None
VERSION = None
GAMEPAD = None
OBS = None
LAST_SCREENSHOT = None
PLAYER_LAST_DIRECTION = 'DOWN'

# --- Helper Functions (from original project) ---

def fuzzy_match(ocr_text, options_list):
    # Get version-specific character equivalences from the config
    equivalences = CONFIG.get('ocr_corrections', {}).get('character_equivalences', {})
    
    def get_substitution_cost(c1, c2):
        if c1 == c2:
            return 0
        if equivalences.get(c1) and c2 in equivalences.get(c1):
            return 0.1
        if equivalences.get(c2) and c1 in equivalences.get(c2):
            return 0.1
        return 1

    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + get_substitution_cost(c1, c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    ocr_text_lower = ocr_text.lower()
    
    best_match = None
    highest_similarity = 0

    for option in options_list:
        if option is None:
            continue
        option_lower = option.lower()
        distance = levenshtein_distance(ocr_text_lower, option_lower)
        max_len = max(len(ocr_text_lower), len(option_lower))
        if max_len == 0:
            similarity = 1.0
        else:
            similarity = 1.0 - (distance / max_len)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = option
    
    if highest_similarity > 0.6:
        return best_match
    else:
        return None

def run_ocr_in_region(frame, x1, y1, x2, y2, preprocess=False, allowlist=None, upscale=False):
    cropped_frame = frame[y1:y2, x1:x2]
    if cropped_frame.size == 0:
        logging.warning(f"Cannot OCR a region with zero size: {x1},{y1},{x2},{y2}")
        return ""

    processed_frame = cropped_frame
    if preprocess:
        gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
        processed_frame = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    frame_to_ocr = processed_frame
    if upscale:
        scale_factor = 2
        frame_to_ocr = cv2.resize(processed_frame, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    easyocr_params = {}
    if allowlist:
        easyocr_params['allowlist'] = allowlist
    
    result = OCR_READER.readtext(frame_to_ocr, **easyocr_params)
    text = ' '.join([item[1] for item in result])
    return text.strip()

def ocr_region(frame, region_name):
    x1, y1, x2, y2 = OCR_REGIONS[region_name]
    preprocess = region_name in ['p1_team_select_text']
    return run_ocr_in_region(frame, x1, y1, x2, y2, preprocess=preprocess)

# --- New Helper Functions ---

def load_configs():
    global CONFIG, TEAMS_CONFIG, OCR_REGIONS, VERSION
    with open("config.yaml", 'r') as f:
        CONFIG = yaml.safe_load(f)
    
    VERSION = CONFIG.get("version")
    if not VERSION:
        logging.error("Version not set in config.yaml")
        sys.exit(1)
        
    version_config = CONFIG.get(VERSION, {})
    teams_config_path = version_config.get("teams_config_path")
    
    with open(teams_config_path, 'r') as f:
        TEAMS_CONFIG = yaml.safe_load(f)
        
    OCR_REGIONS = version_config.get('ocr_regions', {})

def check_process_running(process_name_pattern):
    for proc in psutil.process_iter(['name']):
        if process_name_pattern in proc.info['name']:
            return True
    return False

async def press_key(button, sleep_time=0.2):
    GAMEPAD.press_button(button=button)
    GAMEPAD.update()
    await asyncio.sleep(sleep_time)
    GAMEPAD.release_button(button=button)
    GAMEPAD.update()
    await asyncio.sleep(0.1)

async def press_left_analog(direction, sleep_time=0.2):
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
    GAMEPAD.left_joystick_float(x_value_float=x_val, y_value_float=y_val)
    GAMEPAD.update()
    await asyncio.sleep(sleep_time)
    GAMEPAD.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    GAMEPAD.update()
    await asyncio.sleep(0.1)

async def select_league(leagues, target_league):
    global PLAYER_LAST_DIRECTION
    logging.info(f"Starting league selection for '{target_league}'.")
    while True:
        await asyncio.sleep(1 / 10) # Read screen 10 times a second
        frame = OBS.get_frame()
        if frame is None:
            continue

        p1_league_text = ocr_region(frame, 'p1_league_text')
        p1_current_league = fuzzy_match(p1_league_text, leagues)

        if p1_current_league is None:
            logging.warning(f"LEAGUE_SELECT: Could not match OCR text '{p1_league_text}'. Repeating last action: {PLAYER_LAST_DIRECTION}.")
            await press_left_analog(PLAYER_LAST_DIRECTION, 0.2)
            continue

        if p1_current_league == target_league:
            logging.info(f"LEAGUE_SELECT: On target league '{target_league}'.")
            await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            break
        else:
            try:
                current_index = leagues.index(p1_current_league)
                target_index = leagues.index(target_league)
                if current_index < target_index:
                    logging.info(f"LEAGUE_SELECT: Current '{p1_current_league}' is before '{target_league}', pressing DOWN.")
                    PLAYER_LAST_DIRECTION = 'DOWN'
                    await press_left_analog('DOWN', 0.2)
                else:
                    logging.info(f"LEAGUE_SELECT: Current '{p1_current_league}' is after '{target_league}', pressing UP.")
                    PLAYER_LAST_DIRECTION = 'UP'
                    await press_left_analog('UP', 0.2)
            except ValueError:
                logging.error(f"League '{target_league}' or '{p1_current_league}' not in list. Skipping.")
                PLAYER_LAST_DIRECTION = 'DOWN'
                await press_left_analog('DOWN', 0.2)

async def select_team(all_teams, desired_team):
    global PLAYER_LAST_DIRECTION
    logging.info(f"Starting team selection for '{desired_team}'.")
    desired_team_lower = desired_team.lower().strip('/')
    
    while True:
        await asyncio.sleep(1 / 10)
        frame = OBS.get_frame()
        if frame is None:
            continue

        player1_text = ocr_region(frame, 'p1_team_select_text')
        current_team = fuzzy_match(player1_text.lower()[1:-1], all_teams)

        if current_team is None:
            logging.warning(f"TEAM_SELECT: Could not match OCR text '{player1_text}'. Repeating last action: {PLAYER_LAST_DIRECTION}.")
            await press_left_analog(PLAYER_LAST_DIRECTION, 0.2)
            continue
        
        logging.debug(f"TEAM_SELECT OCR: '{player1_text}' -> Matched: '{current_team}'")

        if current_team.lower() == desired_team_lower:
            logging.info(f"TEAM_SELECT: Desired team '{desired_team}' found, pressing A.")
            await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            break
        elif current_team.lower() < desired_team_lower:
            logging.info(f"TEAM_SELECT: Navigating DOWN for '{desired_team}'. Current: '{current_team}'.")
            PLAYER_LAST_DIRECTION = 'DOWN'
            await press_left_analog('DOWN', 0.2)
        else: # current_team > desired_team
            logging.info(f"TEAM_SELECT: Navigating UP for '{desired_team}'. Current: '{current_team}'.")
            PLAYER_LAST_DIRECTION = 'UP'
            await press_left_analog('UP', 0.2)

async def main():
    global CONFIG, TEAMS_CONFIG, OCR_READER, OCR_REGIONS, VERSION, GAMEPAD, OBS, LAST_SCREENSHOT, PLAYER_LAST_DIRECTION

    # --- Initialization ---
    load_configs()
    GAMEPAD = vg.VX360Gamepad()
    logging.info("Virtual gamepad initialized.")
    
    obs_config = CONFIG.get('obs', {})
    OBS = OBSClient(
        host=obs_config.get('host', 'localhost'),
        port=obs_config.get('port', 4455),
        password=obs_config.get('password', '')
    )
    OBS.connect()
    if not OBS.ws:
        logging.error("Failed to connect to OBS.")
        sys.exit(1)
    logging.info("Connected to OBS.")

    OCR_READER = easyocr.Reader(['en', 'ja'])
    logging.info("EasyOCR reader initialized.")

    # --- Initial Actions ---
    logging.info("Starting initial sequence...")
    await press_left_analog('LEFT')
    await asyncio.sleep(1)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
    logging.info("Waiting for 5 seconds...")
    await asyncio.sleep(5)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
    await asyncio.sleep(1)
    await press_left_analog('DOWN')
    await asyncio.sleep(0.2)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
    await asyncio.sleep(0.2)
    logging.info("Initial sequence complete.")

    # --- Team and Player Loop ---
    leagues = list(TEAMS_CONFIG.keys())
    all_teams_by_league = {}
    selectable_teams_map = {}
    for league_name, teams_list in TEAMS_CONFIG.items():
        if teams_list:
            if league_name not in all_teams_by_league:
                all_teams_by_league[league_name] = []
            for team_data in teams_list:
                team_name = team_data.get("name")
                if team_name:
                    all_teams_by_league[league_name].append(team_name[1:-1])
                    if team_data.get("selectable") is True:
                        if league_name not in selectable_teams_map:
                            selectable_teams_map[league_name] = []
                        selectable_teams_map[league_name].append(team_name)

    for league, teams in selectable_teams_map.items():
        await select_league(leagues, league)
        
        teams_in_current_league = all_teams_by_league.get(league, [])
        sorted_teams = sorted(teams)
        for team_name in sorted_teams:
            await select_team(teams_in_current_league, team_name)
            
            logging.info(f"Processing team: {team_name}")
            team_folder = Path(f"screenshots/{team_name.strip('/')}")
            team_folder.mkdir(parents=True, exist_ok=True)
            LAST_SCREENSHOT = None

            for i in range(23):
                await asyncio.sleep(1)
                logging.info(f"Processing player {i+1}/24 for team {team_name}")

                if not check_process_running("PES20"):
                    logging.error("Game process 'PES20**.exe' not found. Exiting.")
                    sys.exit(1)

                await asyncio.sleep(1/10)
                frame = OBS.get_frame()
                if frame is None:
                    logging.error("Could not get frame from OBS. Exiting.")
                    sys.exit(1)

                # Save screenshot
                screenshot_path = team_folder / f"{i+1:02d}.png"
                cv2.imwrite(str(screenshot_path), frame)

                # Compare with previous screenshot
                if i > 0 and LAST_SCREENSHOT is not None:
                    if np.array_equal(frame, LAST_SCREENSHOT):
                        logging.error(f"PES seems to have frozen on player {i}. Exiting.")
                        sys.exit(1)
                LAST_SCREENSHOT = frame

                # --- Gamepad Actions ---
                await asyncio.sleep(0.2)
                await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
                await asyncio.sleep(0.2)
                for _ in range(7):
                    await press_left_analog('DOWN', 0.1)
                    await asyncio.sleep(0.15)
                await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
                await asyncio.sleep(1)
                
                GAMEPAD.left_trigger_float(1.0)
                GAMEPAD.update()
                await asyncio.sleep(0.25)
                
                logging.info("Starting 5-second video capture...")
                try:
                    # Set recording directory to the team's screenshot folder
                    recording_path = str(team_folder.resolve())
                    OBS.ws.call(obs_requests.SetRecordDirectory(recordDirectory=recording_path))

                    # We will rename the file after recording, so we can ignore SetFilenameFormatting
                    
                    # Start recording
                    OBS.ws.call(obs_requests.StartRecord())
                    logging.info(f"Recording started for player {i+1:02d} in folder '{recording_path}'")

                    # Record for 5 seconds
                    await asyncio.sleep(5)

                    # Stop recording
                    response = OBS.ws.call(obs_requests.StopRecord())
                    logging.info("Recording stopped.")

                    # OBS v28+ returns outputPath in the response. We will rename this file.
                    output_path = response.datain.get('outputPath')
                    if output_path and os.path.exists(output_path):
                        file_extension = os.path.splitext(output_path)[1]
                        desired_filename = f"{i+1:02d}{file_extension}"
                        desired_path = os.path.join(os.path.dirname(output_path), desired_filename)
                        
                        try:
                            # If the desired file already exists, remove it.
                            if os.path.exists(desired_path):
                                os.remove(desired_path)
                            os.rename(output_path, desired_path)
                            logging.info(f"Renamed video to: {desired_path}")
                        except OSError as e:
                            logging.error(f"Error renaming video file: {e}")
                    elif output_path:
                        logging.warning(f"OBS reported video path that does not exist: {output_path}")
                    else:
                        logging.warning("Could not get output path from OBS. File may not have been saved or may require manual renaming.")

                except Exception as e:
                    logging.error(f"An error occurred during OBS recording: {e}")
                GAMEPAD.left_trigger_float(0.0)
                GAMEPAD.update()
                await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.2)
                await asyncio.sleep(0.5)
                await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.2)
                await asyncio.sleep(0.5)
                await press_left_analog('DOWN')
                await asyncio.sleep(0.2)

            logging.info(f"Team {team_name} is OK.")
            await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_B) # Back out to team select

    # --- Finalization ---
    logging.info("All teams processed. Starting finalization sequence.")
    for _ in range(5):
        await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
    await asyncio.sleep(0.2)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    await asyncio.sleep(6)
    await press_key(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
    
    logging.info("Script finished.")
    OBS.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
    finally:
        if OBS and OBS.ws:
            OBS.disconnect()
        logging.info("Cleanup complete.")
