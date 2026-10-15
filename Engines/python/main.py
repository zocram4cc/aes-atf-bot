
import asyncio
import logging
import os
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import vgamepad as vg
from obswebsocket import requests as obs_requests
from obswebsocket import exceptions as obs_exceptions
from python.screen_capture import OBSClient

from python.helpers import (
    load_configs,
    check_process_running,
    press_key,
    press_left_analog,
    select_league,
    select_team,
    SelectionState,
)

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global Variables ---
LAST_SCREENSHOT = None

async def bot():
    parser = argparse.ArgumentParser(description="Automated PES Aesthetic ATF")
    parser.add_argument("--list", required=True, help="Path to the teams list YAML file.")
    parser.add_argument("--version", required=True, help="The version of the game/mod.")
    args = parser.parse_args()

    OBS = None # Initialize OBS to None for graceful error handling
    try:
        # --- Initialization ---
        CONFIG, TEAMS_CONFIG = load_configs(args.list, args.version)

        GAMEPAD = vg.VX360Gamepad()
        logging.info("Virtual gamepad initialized.")

        obs_config = CONFIG.get('obs', {})
        OBS = OBSClient(
            host=obs_config.get('host', 'localhost'),
            port=obs_config.get('port', 4455),
            password=obs_config.get('password', '')
        )
        try:
            OBS.connect()
            if not OBS.ws:
                logging.error("Failed to connect to OBS.")
                sys.exit(1)
            logging.info("Connected to OBS.")
        except obs_exceptions.ConnectionFailure as e:
            logging.error(f"Failed to connect to OBS: {e}")
            logging.error("Please ensure OBS is running and the WebSocket server is enabled in OBS settings (Tools -> WebSocket Server Settings).")
            sys.exit(1)

        OBS.ws.call(obs_requests.SetProfileParameter(
            parameterCategory="SimpleOutput",
            parameterName="RecFormat2",
            parameterValue="mp4"
        ))
        OBS.ws.call(obs_requests.SetProfileParameter(
            parameterCategory="AdvOut",
            parameterName="RecFormat2",
            parameterValue="mp4"
        ))

        selection_state = SelectionState()

        # --- Initial Actions ---
        logging.info("Starting initial sequence...")
        if args.version == "pes15":
            await press_left_analog(GAMEPAD, 'LEFT')
            await asyncio.sleep(1)
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
            logging.info("Waiting for 5 seconds...")
            await asyncio.sleep(5)
        if args.version == "pes17":
            await asyncio.sleep(0.6)
            await press_left_analog(GAMEPAD, 'LEFT')
            await asyncio.sleep(0.6)
            await press_left_analog(GAMEPAD, 'LEFT')
            await asyncio.sleep(0.6)
            await press_left_analog(GAMEPAD, 'UP')
            await asyncio.sleep(0.6)
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
            logging.info("Waiting for 5 seconds...")
            await asyncio.sleep(5)
        if args.version == "pes21":
            for _ in range(3):
                await press_left_analog(GAMEPAD, 'RIGHT')
                await asyncio.sleep(0.2)
            for _ in range(2):
                await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.25)
                await asyncio.sleep(0.3)
            for _ in range(2):
                await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.25)
                await asyncio.sleep(3)
        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
        await asyncio.sleep(1)
        await press_left_analog(GAMEPAD, 'DOWN')
        await asyncio.sleep(0.2)
        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)
        await asyncio.sleep(0.2)
        logging.info("Initial sequence complete.")
        await asyncio.sleep(0.5)

        # --- Team and Player Loop ---
        selectable_teams_map = {}
        team_name_to_id_map = {}
        for league_name, teams_list in TEAMS_CONFIG.items():
            if teams_list:
                for team_index, team_data in enumerate(teams_list):
                    team_name = team_data.get("name")
                    team_id = team_data.get("id")
                    if team_name:
                        if team_id:
                            team_name_to_id_map[team_name] = team_id

                        if team_data.get("selectable") is True:
                            if league_name not in selectable_teams_map:
                                selectable_teams_map[league_name] = []
                            selectable_teams_map[league_name].append((team_index, team_name))

        for league_index, (league, selectable_teams) in enumerate(selectable_teams_map.items()):
            await select_league(GAMEPAD, league_index, selection_state)
            selection_state.current_team_index = 0

            for team_index, team_name in selectable_teams:
                await select_team(GAMEPAD, team_index, selection_state)

                logging.info(f"Processing team: {team_name}")
                team_folder = Path(f"screenshots/{team_name.strip('/')}")
                team_folder.mkdir(parents=True, exist_ok=True)
                global LAST_SCREENSHOT
                LAST_SCREENSHOT = None

                for i in range(23):
                    await asyncio.sleep(1.5)
                    logging.info(f"Processing player {i+1}/23 for team {team_name}")
                    if not check_process_running("PES20"):
                        logging.error("Game process 'PES20**.exe' not found. Exiting.")
                        sys.exit(1)

                    await asyncio.sleep(1/10)
                    if i == 0:
                        await asyncio.sleep(1)
                    frame = OBS.get_frame()
                    if frame is None:
                        logging.error("Could not get frame from OBS. Exiting.")
                        sys.exit(1)

                    # Save screenshot
                    player_id = f"{i+1:02d}"
                    team_id = team_name_to_id_map.get(team_name)
                    if team_id is None:
                        logging.error(f"Could not find team ID for team {team_name}. Exiting.")
                        sys.exit(1)
                    screenshot_filename = f"{team_id}{player_id} - 0 - mainview.jpg"
                    screenshot_path = team_folder / screenshot_filename
                    cv2.imwrite(str(screenshot_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

                    # Compare with previous screenshot
                    if i > 0 and LAST_SCREENSHOT is not None:
                        if np.array_equal(frame, LAST_SCREENSHOT):
                            logging.error(f"PES seems to have frozen on player {i}. Exiting.")
                            sys.exit(1)
                    LAST_SCREENSHOT = frame
                    logging.info(f"Screenshot saved at {screenshot_path}")

                    # --- Navigate to the player's animation menu ---
                    await asyncio.sleep(0.2)
                    await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)  # Select the player
                    await asyncio.sleep(1)
                    for _ in range(2):
                        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, 0.16)
                        await asyncio.sleep(0.15)
                    await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.2)  # Enter the animation/motion menu
                    await asyncio.sleep(1)

                    # --- First video: dribbling animation (one full rotation) ---
                    logging.info("Starting 2.5-second video capture (1 - dribbling)...")
                    try:
                        recording_path = str(team_folder.resolve())
                        OBS.ws.call(obs_requests.SetRecordDirectory(recordDirectory=recording_path))
                        OBS.ws.call(obs_requests.StartRecord())
                        logging.info(f"Recording started for player {i+1:02d} (1 - dribbling) in folder '{recording_path}'")

                        # Wait 0.2s before pressing the trigger/stick
                        await asyncio.sleep(0.2)

                        # Hold the trigger/stick to rotate the player
                        if args.version == "pes15":
                            GAMEPAD.left_trigger_float(1.0)
                            GAMEPAD.update()
                        if args.version == "pes17" or args.version == "pes21":
                            GAMEPAD.right_joystick_float(x_value_float=1.0, y_value_float=0.0)
                            GAMEPAD.update()

                        # Hold for 2.1 seconds of rotation
                        await asyncio.sleep(2.1)

                        # Release the trigger/stick
                        GAMEPAD.left_trigger_float(0.0)
                        GAMEPAD.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
                        GAMEPAD.update()

                        # Record 0.2 more seconds after releasing
                        await asyncio.sleep(0.2)

                        response = OBS.ws.call(obs_requests.StopRecord())
                        logging.info("Recording stopped.")
                        await asyncio.sleep(2)
                        output_path = response.datain.get('outputPath')
                        if output_path and os.path.exists(output_path):
                            file_extension = os.path.splitext(output_path)[1]
                            desired_filename = f"{team_id}{player_id} - 1 - dribbling{file_extension}"
                            desired_path = os.path.join(os.path.dirname(output_path), desired_filename)
                            try:
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

                    # --- Navigate down to the corner kick animation ---
                    for _ in range(4):
                        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.1)
                        await asyncio.sleep(0.1)

                    # --- Second video: corner kick animation ---
                    logging.info("Starting 2.5-second video capture (2 - corner)...")
                    try:
                        recording_path = str(team_folder.resolve())
                        OBS.ws.call(obs_requests.SetRecordDirectory(recordDirectory=recording_path))
                        OBS.ws.call(obs_requests.StartRecord())
                        logging.info(f"Recording started for player {i+1:02d} (2 - corner) in folder '{recording_path}'")
                        await asyncio.sleep(2.5)
                        response = OBS.ws.call(obs_requests.StopRecord())
                        logging.info("Recording stopped.")
                        await asyncio.sleep(2)
                        output_path = response.datain.get('outputPath')
                        if output_path and os.path.exists(output_path):
                            file_extension = os.path.splitext(output_path)[1]
                            desired_filename = f"{team_id}{player_id} - 2 - corner{file_extension}"
                            desired_path = os.path.join(os.path.dirname(output_path), desired_filename)
                            try:
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

                    # --- Back out to the player list ---
                    await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.25)  # Back out of animation menu
                    await asyncio.sleep(0.7)
                    await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.25)  # Back out of player profile
                    await asyncio.sleep(0.7)
                    await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.2)  # Move to next player
                    await asyncio.sleep(0.2)

                logging.info(f"Team {team_name} processed.")
                await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_B) # Back out to team select

        # --- Finalization ---
        logging.info("All teams processed. Starting finalization sequence.")
        for _ in range(5):
            await asyncio.sleep(0.2)
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.2)
            await asyncio.sleep(0.1)
        await asyncio.sleep(2)
        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.2)
        await asyncio.sleep(0.5)
        if args.version == "pes15" or args.version == "pes17":
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        if args.version == "pes21":
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        await asyncio.sleep(0.2)
        await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        await asyncio.sleep(6)
        if args.version == "pes15": # to return to initial mainmenu
            await press_key(GAMEPAD, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        if args.version == "pes17": # to return to initial mainmenu
            for _ in range(2):
                await asyncio.sleep(0.5)
                await press_left_analog(GAMEPAD, 'RIGHT')
        if args.version == "pes21":
            for _ in range(3):
                await press_left_analog(GAMEPAD, 'LEFT')
                await asyncio.sleep(0.2)

        logging.info("Script finished.")
    finally:
        if OBS and OBS.ws:
            OBS.disconnect()

def main():
    try:
        asyncio.run(bot())
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
    finally:
        logging.info("Cleanup complete.")

if __name__ == "__main__":
    main()
