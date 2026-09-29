from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import pygame
import vgamepad as vg

from .deadzone import CrossDeadzoneProfile, clamp


@dataclass
class ControllerState:
    connected_name: str = "None"
    left_raw: tuple[float, float] = (0.0, 0.0)
    left_mapped: tuple[float, float] = (0.0, 0.0)
    right_raw: tuple[float, float] = (0.0, 0.0)
    triggers: tuple[int, int] = (0, 0)
    buttons_pressed: list[str] = field(default_factory=list)
    output_ready: bool = False
    error: str = ""
    detected_devices: list[str] = field(default_factory=list)


class CrossSenseRuntime:
    """Robust DualSense -> Steam Cross 6-83 -> virtual Xbox runtime.

    v6 intentionally goes back to a dedicated polling thread like v3, because that
    was more stable on Tobias' PC than the v4/v5 Tkinter tick-only runtime.
    """

    def __init__(self) -> None:
        self.running = False
        self.profile = CrossDeadzoneProfile()
        self.state = ControllerState()
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.gamepad: Optional[vg.VX360Gamepad] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self, profile: CrossDeadzoneProfile) -> None:
        self.stop()
        self.profile = profile
        with self._lock:
            self.state.error = ""
            self.state.output_ready = False
            self.state.connected_name = "None"

        try:
            pygame.init()
            pygame.joystick.init()
            # Give SDL a moment to refresh USB devices.
            for _ in range(4):
                pygame.event.pump()
                time.sleep(0.03)

            self.joystick = self._find_physical_controller()
            if self.joystick is None:
                names = self._device_names()
                with self._lock:
                    self.state.detected_devices = names
                    self.state.error = "No physical DualSense found. Detected: " + (", ".join(names) if names else "none")
                return

            # Keep input status even if virtual output fails, so troubleshooting is clear.
            with self._lock:
                self.state.connected_name = self.joystick.get_name() or "Controller"
                self.state.detected_devices = self._device_names()

            self.gamepad = vg.VX360Gamepad()
            with self._lock:
                self.state.output_ready = True
                self.state.error = ""

            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        except Exception as exc:
            self.running = False
            with self._lock:
                self.state.error = f"Start failed: {exc}"
                self.state.output_ready = False

    def stop(self) -> None:
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None

        if self.gamepad is not None:
            try:
                self.gamepad.reset()
                self.gamepad.update()
                time.sleep(0.03)
            except Exception:
                pass
            try:
                del self.gamepad
            except Exception:
                pass
        self.gamepad = None
        with self._lock:
            self.state.output_ready = False

    def shutdown(self) -> None:
        self.stop()
        try:
            pygame.joystick.quit()
            pygame.quit()
        except Exception:
            pass

    def poll_and_output(self) -> ControllerState:
        # UI calls this every frame. Actual controller work happens in the thread.
        with self._lock:
            return ControllerState(
                connected_name=self.state.connected_name,
                left_raw=self.state.left_raw,
                left_mapped=self.state.left_mapped,
                right_raw=self.state.right_raw,
                triggers=self.state.triggers,
                buttons_pressed=list(self.state.buttons_pressed),
                output_ready=self.state.output_ready,
                error=self.state.error,
                detected_devices=list(self.state.detected_devices),
            )

    def _run_loop(self) -> None:
        delay = 1.0 / 250.0
        while self.running and self.joystick is not None and self.gamepad is not None:
            try:
                pygame.event.pump()
                lx = _axis(self.joystick, 0)
                ly = _axis(self.joystick, 1)
                rx = _axis(self.joystick, 2)
                ry = _axis(self.joystick, 3)
                lm_x, lm_y = self.profile.map_left_stick(lx, ly)

                lt = _trigger_to_0_255(_axis(self.joystick, 4, -1.0))
                rt = _trigger_to_0_255(_axis(self.joystick, 5, -1.0))

                # XInput uses positive Y up. Pygame DualSense usually gives up as -Y.
                self.gamepad.left_joystick_float(x_value_float=clamp(lm_x), y_value_float=clamp(-lm_y))
                self.gamepad.right_joystick_float(x_value_float=clamp(rx), y_value_float=clamp(-ry))
                self.gamepad.left_trigger(value=lt)
                self.gamepad.right_trigger(value=rt)

                pressed_names: list[str] = []
                for pygame_button, xbox_button in BUTTON_MAP.items():
                    pressed = False
                    try:
                        pressed = pygame_button < self.joystick.get_numbuttons() and bool(self.joystick.get_button(pygame_button))
                    except Exception:
                        pressed = False
                    if pressed:
                        self.gamepad.press_button(button=xbox_button)
                        pressed_names.append(BUTTON_NAMES.get(pygame_button, str(pygame_button)))
                    else:
                        self.gamepad.release_button(button=xbox_button)

                self._output_dpad()
                self.gamepad.update()

                with self._lock:
                    self.state.left_raw = (lx, ly)
                    self.state.left_mapped = (lm_x, lm_y)
                    self.state.right_raw = (rx, ry)
                    self.state.triggers = (lt, rt)
                    self.state.buttons_pressed = pressed_names
                    self.state.connected_name = self.joystick.get_name() or "Controller"
                    self.state.output_ready = True
                    self.state.error = ""
            except Exception as exc:
                with self._lock:
                    self.state.error = str(exc)
            time.sleep(delay)

    def _device_names(self) -> list[str]:
        names: list[str] = []
        try:
            count = pygame.joystick.get_count()
            for idx in range(count):
                js = pygame.joystick.Joystick(idx)
                js.init()
                names.append(js.get_name() or f"Controller {idx}")
        except Exception:
            pass
        return names

    def _find_physical_controller(self):
        names = []
        count = pygame.joystick.get_count()
        fallback = None
        for idx in range(count):
            js = pygame.joystick.Joystick(idx)
            js.init()
            name = js.get_name() or f"Controller {idx}"
            names.append(name)
            lowered = name.lower()

            # Avoid feeding CrossSense from its own virtual Xbox output.
            is_virtual_xbox = "xbox 360" in lowered or "xinput" in lowered or "vigem" in lowered
            if is_virtual_xbox:
                continue

            if fallback is None:
                fallback = js
            if "dualsense" in lowered or "wireless controller" in lowered or "ps5" in lowered or "sony" in lowered:
                with self._lock:
                    self.state.detected_devices = names
                return js

        with self._lock:
            self.state.detected_devices = names
        return fallback

    def _output_dpad(self) -> None:
        if self.gamepad is None or self.joystick is None:
            return
        for btn in (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT):
            self.gamepad.release_button(button=btn)
        try:
            if self.joystick.get_numhats() > 0:
                hx, hy = self.joystick.get_hat(0)
                if hy > 0:
                    self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                elif hy < 0:
                    self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                if hx < 0:
                    self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                elif hx > 0:
                    self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        except Exception:
            pass


def _axis(js: pygame.joystick.Joystick, index: int, default: float = 0.0) -> float:
    try:
        if index >= js.get_numaxes():
            return default
        value = float(js.get_axis(index))
        if abs(value) < 0.003:
            return 0.0
        return clamp(value)
    except Exception:
        return default


def _trigger_to_0_255(value: float) -> int:
    normalized = (clamp(value) + 1.0) / 2.0
    if normalized < 0.02:
        normalized = 0.0
    return int(round(clamp(normalized, 0.0, 1.0) * 255))


BUTTON_NAMES = {
    0: "A/Cross",
    1: "B/Circle",
    2: "X/Square",
    3: "Y/Triangle",
    4: "LB/L1",
    5: "RB/R1",
    6: "Back/Create",
    7: "Start/Options",
    8: "Guide/PS",
    9: "LS/L3",
    10: "RS/R3",
}

BUTTON_MAP = {
    0: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    1: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    2: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    3: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    4: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    5: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    6: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    7: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    8: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    9: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    10: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
}
