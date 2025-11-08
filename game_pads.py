import vgamepad as vg
import logging
import asyncio

logger = logging.getLogger(__name__)

class Gamepad:
    def __init__(self):
        self._pad = vg.VX360Gamepad()
        self._lock = asyncio.Lock()

    async def press_button(self, button):
        logger.debug(f"Gamepad: Pressing button {button}")
        async with self._lock:
            await asyncio.to_thread(self._pad.press_button, button=button)
            await asyncio.to_thread(self._pad.update)

    async def release_button(self, button):
        logger.debug(f"Gamepad: Releasing button {button}")
        async with self._lock:
            await asyncio.to_thread(self._pad.release_button, button=button)
            await asyncio.to_thread(self._pad.update)

    async def left_trigger(self, value):
        logger.debug(f"Gamepad: Setting left trigger to {value}")
        async with self._lock:
            await asyncio.to_thread(self._pad.left_trigger, value=value)
            await asyncio.to_thread(self._pad.update)

    async def left_joystick_float(self, x_value_float, y_value_float):
        logger.debug(f"Gamepad: Setting left joystick to ({x_value_float}, {y_value_float})")
        async with self._lock:
            await asyncio.to_thread(self._pad.left_joystick_float, x_value_float=x_value_float, y_value_float=y_value_float)
            await asyncio.to_thread(self._pad.update)

    async def release_all_buttons(self):
        logger.debug("Gamepad: Releasing all buttons and resetting joysticks/triggers.")
        async with self._lock:
            # Release all buttons (common XUSB_BUTTONs)
            for button in [
                vg.XUSB_BUTTON.XUSB_GAMEPAD_A, vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_X, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                vg.XUSB_BUTTON.XUSB_GAMEPAD_START, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            ]:
                await asyncio.to_thread(self._pad.release_button, button=button)
            
            # Reset joysticks and triggers
            await asyncio.to_thread(self._pad.left_joystick_float, x_value_float=0.0, y_value_float=0.0)
            await asyncio.to_thread(self._pad.right_joystick_float, x_value_float=0.0, y_value_float=0.0)
            await asyncio.to_thread(self._pad.left_trigger, value=0)
            await asyncio.to_thread(self._pad.right_trigger, value=0)
            
            await asyncio.to_thread(self._pad.update)

    async def reset(self):
        logger.debug("Gamepad: Resetting gamepad.")
        async with self._lock:
            await asyncio.to_thread(self._pad.reset)
            await asyncio.to_thread(self._pad.update)

    async def close(self):
        logger.debug("Gamepad: Closing gamepad.")
        async with self._lock:
            try:
                self._pad.reset()
                self._pad.update()
            except Exception as e:
                logger.warning(f"Error while releasing gamepad: {e}")

class GamePads:
    def __init__(self, num_gamepads=2):
        self.gamepads = []
        for i in range(num_gamepads):
            logger.info(f"Creating gamepad {i+1}")
            self.gamepads.append(Gamepad())
            logger.info(f"Gamepad {i+1} created")
            if i < num_gamepads - 1:
                import time
                time.sleep(0.5) # Increased delay

    async def press_button_all(self, button):
        await asyncio.gather(*[pad.press_button(button) for pad in self.gamepads])

    async def release_button_all(self, button):
        await asyncio.gather(*[pad.release_button(button) for pad in self.gamepads])

    async def left_joystick_float_all(self, x_value_float, y_value_float):
        await asyncio.gather(*[pad.left_joystick_float(x_value_float, y_value_float) for pad in self.gamepads])

    async def release_all_buttons(self):
        logger.info("Releasing all gamepad buttons and resetting joysticks/triggers.")
        await asyncio.gather(*[pad.release_all_buttons() for pad in self.gamepads])

    async def close_all(self):
        logger.info("Releasing and unloading gamepads")
        await asyncio.gather(*[pad.close() for pad in self.gamepads])

