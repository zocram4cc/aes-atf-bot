# Automated PES Asset Scraper

This script automates the process of capturing screenshots and video clips of players in Pro Evolution Soccer (PES) for aesthetics checking. It uses computer vision (OCR) to navigate the game menus and OBS Studio to record the screen.

## Requirements

-   Python 3.x
-   OBS Studio
-   [ViGEmBus Driver](https://github.com/ViGEm/ViGEmBus/releases)
-   No physical controllers plugged in.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```

2.  **Install Python dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows (PowerShell):
    .\venv\Scripts\activate
    # On Windows (Command Prompt):
    venv\Scripts\activate.bat
    ```
    Then, install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install ViGEmBus Driver (Windows Only):**
    The virtual gamepad library (`vgamepad`) requires the ViGEmBus driver to be installed on your system.
    -   Download the latest release from the [ViGEmBus releases page](https://github.com/ViGEm/ViGEmBus/releases).
    -   Run the installer and follow the on-screen instructions.

4.  **Configure OBS Studio and Enable WebSocket Server:**
    The script communicates with OBS Studio via the WebSocket protocol and relies on specific video settings.
    -   **OBS Video Settings:** Ensure your OBS canvas resolution is set to `1920x1080`. Go to `Settings -> Video -> Base (Canvas) Resolution`.
    -   **Window Capture:** Add a "Window Capture" source for your PES game. Make sure this source is set to full screen and is unobstructed by other elements in your OBS scene. Make sure the scene is selected and active.
    -   **Enable WebSocket Server:**
        -   Go to `Tools -> WebSocket Server Settings`.
        -   Check the "Enable WebSocket Server" box.
        -   You can leave the server port and password to their default values. If you change them, make sure to update the `config.yaml` file accordingly.
    **PLEASE NOTE**: The script will change your OBS's recording output folder and will **not** restore it to what it was originally set. Keep this in mind.

5.  **Unplug physical controllers:**
    To avoid conflicts with the virtual gamepad, it is required to unplug any physical controllers before running the script.

## Usage

To run the script, open the desired PES at the main menu (don't move the cursor), add it to the current OBS scene, then use the following command:

```bash
python main.py --version <game_version> --list <path_to_teams_list>
```

-   `<game_version>`: The version of the game/mod you are running (e.g., `pes15`, `pes21`). This should correspond to a key in your `config.yaml`. NOTE: For now, only PES15 and 21 are actually implemented.
-   `<path_to_teams_list>`: The path to the YAML file containing the list of teams to process (e.g., `teams_lists/vtlxpo.yaml`).

Example:
```bash
python main.py --version pes21 --list teams_lists/vtlxpo.yaml
```

## Building with PyInstaller

You can create a standalone executable using PyInstaller.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Build the executable:**
    Run the following command in the root of the project directory:
    ```bash
    pyinstaller --onefile --name "ATF-Bot" main.py
    ```
    -   `--onefile`: Creates a single executable file.
    -   `--name`: Sets the name of the executable.

    The executable will be located in the `dist` folder.

    **Note:** PyInstaller might not automatically include all the necessary data files (like `config.yaml`, `teams_lists/`, etc.). You may need to copy these files to the same directory as the executable, or use the `--add-data` flag in the PyInstaller command to bundle them. For example:
    ```bash
    pyinstaller --onefile --name "ATF-Bot" --add-data "config.yaml:." --add-data "teams_lists:teams_lists" main.py
    ```
