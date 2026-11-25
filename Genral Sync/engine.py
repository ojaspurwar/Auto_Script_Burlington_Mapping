"""
Genral Sync - Universal Sequence Automation Engine
Works on any Windows screen resolution and DPI scaling.
Supports: click, wait, drag (words or scrollbars), scroll, and move steps.
"""

import ctypes
import json
import sys
import threading
import time
import pyautogui

# Enable Per-Monitor DPI Awareness so coordinates match actual screen pixels
# across 100%, 125%, 150%, etc. on any resolution.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

pyautogui.FAILSAFE = True  # Move mouse to any screen corner to abort immediately
pyautogui.PAUSE = 0.03


def get_screen_size():
    """Return (width, height) of the primary screen."""
    size = pyautogui.size()
    return size.width, size.height


class SequenceEngine:
    def __init__(self, status_cb=None, step_cb=None, countdown_cb=None, done_cb=None):
        self.status_cb = status_cb or (lambda msg: print(f"[*] {msg}"))
        self.step_cb = step_cb or (lambda idx, cycle: None)
        self.countdown_cb = countdown_cb or (lambda rem, tot, lbl: None)
        self.done_cb = done_cb or (lambda: None)

        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self._thread = None

    def start(self, steps, repeat_count=0):
        """
        Run `steps` in a background thread.
        repeat_count == 0 means loop forever until stopped.
        """
        if self.is_running or not steps:
            return
        self.is_running = True
        self.is_paused = False
        self.stop_requested = False
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(list(steps), int(repeat_count)),
            daemon=True,
        )
        self._thread.start()

    def pause(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        self.status_cb("PAUSED" if self.is_paused else "RESUMED")

    def stop(self):
        self.stop_requested = True
        self.is_running = False
        self.is_paused = False
        self.status_cb("Stopping...")

    def _check_control(self):
        while self.is_paused and not self.stop_requested:
            time.sleep(0.15)
        if self.stop_requested:
            raise KeyboardInterrupt("Stopped by user")

    def _safe_sleep(self, seconds):
        end_time = time.time() + max(0.0, float(seconds))
        while time.time() < end_time:
            self._check_control()
            time.sleep(min(0.1, max(0.0, end_time - time.time())))

    def _wait_countdown(self, seconds, label="Waiting"):
        total = max(0, int(round(seconds)))
        if total == 0:
            self._safe_sleep(seconds)
            return
        for rem in range(total, -1, -1):
            self.countdown_cb(rem, total, label)
            if rem > 0:
                self._safe_sleep(1.0)

    def _execute_step(self, step):
        self._check_control()
        stype = step.get("type", "click")
        label = step.get("label", stype.title())

        if stype == "click":
            x, y = int(step["x"]), int(step["y"])
            button = step.get("button", "left")
            clicks = int(step.get("clicks", 1))
            self.status_cb(f"Click ({x}, {y}) - {label}")
            pyautogui.moveTo(x, y, duration=0.22, tween=pyautogui.easeOutQuad)
            time.sleep(0.08)
            pyautogui.click(x, y, clicks=clicks, button=button)
            self._safe_sleep(float(step.get("after", 0.3)))

        elif stype == "wait":
            secs = float(step.get("seconds", 1))
            self.status_cb(f"Waiting {secs:g}s - {label}")
            self._wait_countdown(secs, label=label or "Waiting")

        elif stype == "drag":
            x1, y1 = int(step["x1"]), int(step["y1"])
            x2, y2 = int(step["x2"]), int(step["y2"])
            dur = float(step.get("duration", 0.5))
            self.status_cb(f"Drag ({x1},{y1}) -> ({x2},{y2}) - {label}")
            pyautogui.moveTo(x1, y1, duration=0.22, tween=pyautogui.easeOutQuad)
            time.sleep(0.12)
            pyautogui.mouseDown(button="left")
            time.sleep(0.12)
            # Small nudge helps browser HTML5 dragstart fire reliably
            pyautogui.moveTo(x1 + 5, y1 + 3, duration=0.08)
            time.sleep(0.08)
            pyautogui.moveTo(x2, y2, duration=dur, tween=pyautogui.easeInOutQuad)
            time.sleep(0.2)
            pyautogui.mouseUp(button="left")
            self._safe_sleep(float(step.get("after", 0.3)))

        elif stype == "scroll":
            x, y = int(step["x"]), int(step["y"])
            amount = int(step.get("amount", -300))
            self.status_cb(f"Scroll {amount} at ({x}, {y}) - {label}")
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.08)
            pyautogui.scroll(amount)
            self._safe_sleep(float(step.get("after", 0.3)))

        elif stype == "move":
            x, y = int(step["x"]), int(step["y"])
            self.status_cb(f"Move to ({x}, {y}) - {label}")
            pyautogui.moveTo(x, y, duration=0.25, tween=pyautogui.easeOutQuad)
            self._safe_sleep(float(step.get("after", 0.2)))

    def _run_loop(self, steps, repeat_count):
        cycle = 0
        try:
            while not self.stop_requested:
                cycle += 1
                self.status_cb(f"=== Cycle #{cycle} ===")
                for idx, step in enumerate(steps):
                    self.step_cb(idx, cycle)
                    self._execute_step(step)
                if repeat_count > 0 and cycle >= repeat_count:
                    self.status_cb(f"Completed {repeat_count} cycle(s).")
                    break
        except KeyboardInterrupt:
            self.status_cb("Stopped by user.")
        except pyautogui.FailSafeException:
            self.status_cb("ABORTED: Mouse moved to screen corner (Fail-Safe).")
        except Exception as exc:
            self.status_cb(f"Error: {exc}")
        finally:
            self.is_running = False
            self.is_paused = False
            self.step_cb(-1, cycle)
            self.done_cb()


def main():
    if len(sys.argv) < 2:
        print("Usage: python engine.py <profile.json> [repeat_count]")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = data.get("steps", data) if isinstance(data, dict) else data
    repeat_count = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"Loaded {len(steps)} steps. Starting in 3 seconds...")
    time.sleep(3)
    engine = SequenceEngine()
    engine.start(steps, repeat_count=repeat_count)
    try:
        while engine.is_running:
            time.sleep(0.3)
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    main()
