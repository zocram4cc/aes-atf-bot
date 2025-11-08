import base64
import io
import cv2
import numpy as np
import logging
from PIL import Image

# OBS WebSocket API client
from obswebsocket import obsws, requests

import os

logger = logging.getLogger(__name__)

class OBSClient:
    def __init__(self, host="localhost", port=4455, password="", source_name="Scene"):
        self.ws = obsws(host, port, password)
        self.source_name = source_name
        self.capture_scene_name = os.environ.get('OBS_CAPTURE_SCENE')
        if self.capture_scene_name:
            logger.info(f"OBS_CAPTURE_SCENE environment variable set. Capturing from scene: {self.capture_scene_name}")

    def connect(self):
        self.ws.connect()
        logger.info("Connected to OBS")

    def disconnect(self):
        self.ws.disconnect()
        logger.info("Disconnected from OBS")

    def get_frame(self):
        try:
            if self.capture_scene_name:
                scene_name = self.capture_scene_name
                logger.debug(f"Getting screenshot from specified scene: {scene_name}")
            else:
                scene_response = self.ws.call(requests.GetCurrentProgramScene())
                scene_name = scene_response.datain['currentProgramSceneName']
                logger.debug(f"Getting screenshot from active scene: {scene_name}")

            screenshot_request = requests.GetSourceScreenshot(
                sourceName=scene_name,
                imageFormat='jpeg'
            )

            screenshot_response = self.ws.call(screenshot_request)
            b64_data = screenshot_response.datain['imageData']
            # logger.debug(f"Raw image data: {b64_data[:100]}...") # Removed full image data logging
            if ',' in b64_data:
                b64_data = b64_data.split(',', 1)[1]
            img_data = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(img_data))
            frame = np.array(img)
            logger.debug(f"Successfully captured frame with dimensions: {frame.shape}")
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to get frame: {e}")
            return None
