# Prepare a list of dependencies as dictionaries
DEPENDENCIES: list[dict[str, str]] = [
    {
        "name_package": "numpy",
        "version":      "any",
        "name_pip":     "numpy",
        "name_user":    "NumPy (matrix operations)",
    },
    {
        "name_package": "cv2",
        "version":      "any",
        "name_pip":     "opencv-python",
        "name_user":    "OpenCV (computer vision)",
    },
    {
        "name_package": "PIL",
        "version":      "any",
        "name_pip":     "Pillow",
        "name_user":    "Pillow (image processing)",
    },
    {
        "name_package": "obswebsocket",
        "version":      "any",
        "name_pip":     "obs-websocket-py",
        "name_user":    "OBS WebSocket (OBS remote control)",
    },
    {
        "name_package": "yaml",
        "version":      "any",
        "name_pip":     "PyYAML",
        "name_user":    "PyYAML (YAML parsing)",
    },
    {
        "name_package": "vgamepad",
        "version":      "any",
        "name_pip":     "vgamepad",
        "name_user":    "vgamepad (virtual gamepad)",
    },
    {
        "name_package": "psutil",
        "version":      "any",
        "name_pip":     "psutil",
        "name_user":    "psutil (system and process utilities)",
    },
    {
        "name_package": "rich",
        "version":      "any",
        "name_pip":     "rich",
        "name_user":    "Rich (rich text console output)",
    },
]
