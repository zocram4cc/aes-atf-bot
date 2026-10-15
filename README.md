# Automated PES Asset Scraper

This script automates the process of capturing screenshots and video clips of players in Pro Evolution Soccer (PES) for aesthetics checking. It uses OBS Studio to record the screen.

## Installation

1.  **Installing ViGEmBus Driver (Windows Only):**
    The virtual gamepad library (`vgamepad`) requires the ViGEmBus driver to be installed on your system.
    -   Run "0_install_driver.exe" and follow the on-screen instructions.

2.  **Configuring OBS Studio:**
    The script communicates with OBS Studio via the WebSocket protocol and relies on specific video settings.
    -   **Video Settings:**
        -   Go to `Settings -> Video -> Base (Canvas) Resolution`.
        -   Ensure your OBS canvas resolution is set to at least `1280x720`.
    -   **Window Capture:**
        -   Add a "Window Capture" or "Game Capture" source for your PES game.
        -   Make sure this source is set to full screen and is unobstructed by other elements in your OBS scene.
        -   Make sure the scene is selected and active.
    -   **Enable WebSocket Server:**
        -   Go to `Tools -> WebSocket Server Settings`.
        -   Check the "Enable WebSocket Server" box.
        -   You can leave the server port at 4455. Turn off "Enable Authentication".
    -   **Recording Settings:**
        -   The script will change the recording path and will **not** restore it to what it was originally set.  
            If you want to preserve it, go to `Settings -> Output -> Recording` and copy it to some txt file before running the script.  
        -   The script will also change the recording format to "MP4", to allow the videos to be posted to Discord.

3.  **Unplugging physical controllers:**
    To avoid conflicts with the virtual gamepad, it is required to unplug any physical controllers before running the script.
    If you run into input issues, try setting the input type to XInput in the PES settings exe.

## Usage

To run the script:
- Open the desired PES and go to the main menu.  
  (don't move the cursor from the starting position)
- Add it to the current OBS scene.
- Run the "1_run_atf_bot.bat" script.
- Watch the magic unfold.

Once it's finished, the script will disconnect from OBS and exit.  
You can then find the screenshots and videos in the "screenshots" folder.

## Advanced Usage

To run the bot on a different version of PES, you can use the following command:

```bash
python Engines/python/main.py --version <game_version> --list <path_to_teams_list>
```

-   `<game_version>`: The version of the game/mod you are running (e.g., `pes15`, `pes21`). This should correspond to a key in your `config.yaml`. NOTE: For now, only PES15 and 21 are actually implemented.
-   `<path_to_teams_list>`: The path to the YAML file containing the list of teams to process (e.g., `teams_lists/vtlxpo.yaml`).

Example:
```bash
python Engines/python/main.py --version pes21 --list teams_lists/vtlxpo.yaml
```
