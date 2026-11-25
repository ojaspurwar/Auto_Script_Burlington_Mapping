"""
BurlingtonEnglish Automation Engine: Clicker, Mover & Drag-and-Drop Runner.
Features:
- Windows DPI awareness for 100% pixel accuracy.
- 10-second loading delay whenever navigating to ANY section.
- Physical scrollbar thumb dragging for reliable scrolling on custom JS/CSS scrollbars.
- HTML5-compatible drag-and-drop for word pills into target slots.
"""

import ctypes
import os
import sys
import time
import threading
import pyautogui

# Set DPI awareness so coordinates are pixel-perfect on Windows 10/11
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# PyAutoGUI safety configuration
pyautogui.FAILSAFE = True  # Move mouse to any screen corner to immediately abort!
pyautogui.PAUSE = 0.05

import config
import pill_detector


class AutoClickerEngine:
    def __init__(self, status_callback=None, countdown_callback=None):
        self.status_cb = status_callback or self._default_status
        self.countdown_cb = countdown_callback or self._default_countdown
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self._thread = None
        self.cycle_count = 0

    def _default_status(self, msg):
        print(f"[*] {msg}")

    def _default_countdown(self, remaining, total, label="Timer"):
        mins, secs = divmod(remaining, 60)
        sys.stdout.write(f"\r[{label}] {mins:02d}:{secs:02d} remaining... ")
        sys.stdout.flush()
        if remaining == 0:
            print(f"\r[{label}] Done!                                     ")

    def log(self, msg):
        self.status_cb(msg)

    def start(self):
        """Start the automation loop in a background thread."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self.stop_requested = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def pause(self):
        """Pause or unpause the loop."""
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "RESUMED"
        self.log(f"Automation {status}.")

    def stop(self):
        """Stop the automation loop."""
        self.stop_requested = True
        self.is_running = False
        self.is_paused = False
        self.log("Stopping automation...")

    def _check_control(self):
        """Check if stopped or paused, handle pause sleep."""
        while self.is_paused and not self.stop_requested:
            time.sleep(0.2)
        if self.stop_requested:
            raise KeyboardInterrupt("Stopped by user")

    def _safe_sleep(self, duration):
        """Sleep in small intervals to respond immediately to stop/pause."""
        elapsed = 0.0
        interval = 0.1
        while elapsed < duration:
            self._check_control()
            time.sleep(interval)
            elapsed += interval

    def _wait_with_countdown(self, seconds, label="Waiting"):
        """Wait for `seconds` with second-by-second countdown."""
        for remaining in range(seconds, -1, -1):
            self.countdown_cb(remaining, seconds, label)
            if remaining > 0:
                self._safe_sleep(1.0)

    def _click(self, x, y, delay_after=None):
        """Move smoothly and click coordinate."""
        self._check_control()
        pyautogui.moveTo(x, y, duration=0.25, tween=pyautogui.easeOutQuad)
        time.sleep(0.1)
        pyautogui.click(x, y)
        self._safe_sleep(delay_after if delay_after is not None else config.CLICK_DELAY)

    def _drag_scrollbar(self, start_x, start_y, end_x, end_y, duration=0.5):
        """Drag a custom scrollbar thumb smoothly from start to end."""
        self._check_control()
        pyautogui.moveTo(start_x, start_y, duration=0.25)
        time.sleep(0.15)
        pyautogui.mouseDown(button="left")
        time.sleep(0.15)
        pyautogui.moveTo(end_x, end_y, duration=duration, tween=pyautogui.easeInOutQuad)
        time.sleep(0.2)
        pyautogui.mouseUp(button="left")
        time.sleep(0.3)

    def _drag_drop(self, src_x, src_y, dst_x, dst_y):
        """Reliable HTML5 drag-and-drop for words/cards into slots."""
        self._check_control()
        # Move to source word
        pyautogui.moveTo(src_x, src_y, duration=0.25, tween=pyautogui.easeOutQuad)
        time.sleep(0.15)
        # Mouse down
        pyautogui.mouseDown(button="left")
        time.sleep(0.15)
        # Slight nudge to trigger browser dragstart event
        pyautogui.moveTo(src_x + 6, src_y + 4, duration=0.1)
        time.sleep(0.1)
        # Move smoothly to destination slot
        pyautogui.moveTo(dst_x, dst_y, duration=config.DRAG_DURATION, tween=pyautogui.easeInOutQuad)
        time.sleep(0.25)  # Pause over drop slot for DOM dragover
        # Mouse up (drop)
        pyautogui.mouseUp(button="left")
        time.sleep(0.25)

    def _dismiss_modal_if_present(self):
        """Dismiss 'Do you want to correct yourself?' modal if it appears."""
        try:
            img = pyautogui.screenshot()
            if pill_detector.is_modal_popup_visible(img):
                nx, ny = config.MODAL_NO_BUTTON
                self.log(f"[!] Popup detected — clicking 'No' at ({nx}, {ny}) to continue...")
                self._click(nx, ny, delay_after=1.0)
        except Exception as e:
            self.log(f"[!] Modal check skipped: {e}")

    def _run_loop(self):
        self.log("Automation running. (Move mouse to screen corner to abort)")
        self.cycle_count = 0

        try:
            while not self.stop_requested:
                self.cycle_count += 1
                self.log(f"=== Starting Cycle #{self.cycle_count} ===")

                # ----------------------------------------------------
                # STEP 1: SECTION 3 (Click 3, wait 10s to load, click Play, wait 1:15m)
                # ----------------------------------------------------
                self.log("[Step 1] Navigating to Section 3...")
                t3_x, t3_y = config.TAB_COORDINATES[3]
                self._click(t3_x, t3_y, delay_after=0.5)

                self.log(f"[Step 1] Waiting {config.SECTION_LOAD_WAIT}s for Section 3 to fully load...")
                self._wait_with_countdown(config.SECTION_LOAD_WAIT, label="Sec 3 Loading")

                play_x, play_y = config.SEC3_PLAY_BUTTON
                self.log(f"[Step 1] Clicking Play button at ({play_x}, {play_y})...")
                self._click(play_x, play_y, delay_after=0.5)

                total_wait = config.SEC3_WAIT_SECONDS
                self.log(f"[Step 1] Audio playing... Waiting 1:15m ({total_wait}s)...")
                self._wait_with_countdown(total_wait, label="Sec 3 Audio Wait")

                # ----------------------------------------------------
                # STEP 2: SECTION 4 (Click 4, wait 10s to load, scroll down)
                # ----------------------------------------------------
                self.log("[Step 2] Navigating to Section 4...")
                t4_x, t4_y = config.TAB_COORDINATES[4]
                self._click(t4_x, t4_y, delay_after=0.5)

                self.log(f"[Step 2] Waiting {config.SECTION_LOAD_WAIT}s for Section 4 to fully load...")
                self._wait_with_countdown(config.SECTION_LOAD_WAIT, label="Sec 4 Loading")

                self.log("[Step 2] Scrolling Section 4 (dragging scrollbar & wheel)...")
                # Drag scrollbar directly
                sx1, sy1 = config.SEC4_SCROLLBAR_START
                sx2, sy2 = config.SEC4_SCROLLBAR_END
                self._drag_scrollbar(sx1, sy1, sx2, sy2, duration=0.6)
                # Also wheel scroll in middle to guarantee scroll event
                mid_x, mid_y = config.SCREEN_MID
                pyautogui.moveTo(mid_x, mid_y, duration=0.2)
                pyautogui.scroll(-300)

                self.log(f"[Step 2] Scrolled down. Waiting {config.SEC4_WAIT_SECONDS}s...")
                self._safe_sleep(config.SEC4_WAIT_SECONDS)

                # ----------------------------------------------------
                # STEP 3: SECTION 5 (Click 5, wait 10s, RESET FIRST, then scroll, drag, check)
                # ----------------------------------------------------
                self.log("[Step 3] Navigating to Section 5...")
                t5_x, t5_y = config.TAB_COORDINATES[5]
                self._click(t5_x, t5_y, delay_after=0.5)

                self.log(f"[Step 3] Waiting {config.SECTION_LOAD_WAIT}s for Section 5 to fully load...")
                self._wait_with_countdown(config.SECTION_LOAD_WAIT, label="Sec 5 Loading")

                rst_x, rst_y = config.RESET_BUTTON
                self.log("[Step 3] Clicking Reset button first (to avoid resetting scroll)...")
                self._click(rst_x, rst_y, delay_after=1.2)

                self.log("[Step 3] Now scrolling Section 5 (holding scrollbar 1588,584 -> 1590,649)...")
                s5_start_x, s5_start_y = config.SEC5_SCROLLBAR_START
                s5_end_x, s5_end_y = config.SEC5_SCROLLBAR_END
                self._drag_scrollbar(s5_start_x, s5_start_y, s5_end_x, s5_end_y, duration=0.5)
                self._safe_sleep(config.SEC5_SCROLL_DELAY)

                self.log("[Step 3] Detecting shuffled pill positions on screen...")
                try:
                    screen_img = pyautogui.screenshot()
                    pill_map, info = pill_detector.detect_pills_from_image(screen_img)
                    self.log(f"  -> Detected: {', '.join(info)}")
                    for name in ("style", "technique", "opinion", "interpretation"):
                        px, py = pill_map[name]
                        sx, sy = config.SEC5_SLOT_TARGETS[name]
                        self.log(f"  -> Dragging '{name}' ({px},{py}) ➔ ({sx},{sy})...")
                        self._drag_drop(px, py, sx, sy)
                        self._safe_sleep(0.3)
                except Exception as detect_err:
                    self.log(f"[!] Pill detection fallback ({detect_err})...")
                    for p_idx, s_idx in config.SEC5_DRAG_PAIRS:
                        px, py = config.SEC5_PILLS[p_idx]
                        sx, sy = config.SEC5_SLOTS[s_idx]
                        self.log(f"  -> Pill #{p_idx+1} ({px},{py}) ➔ Slot #{s_idx+1} ({sx},{sy})...")
                        self._drag_drop(px, py, sx, sy)
                        self._safe_sleep(0.3)

                chk_x, chk_y = config.CHECK_BUTTON
                self.log("[Step 3] Clicking Check button...")
                self._click(chk_x, chk_y, delay_after=config.TRANSITION_DELAY)
                self._dismiss_modal_if_present()

                # ----------------------------------------------------
                # STEP 4: SECTION 6 (Click 6, wait 10s, reset, do question, check)
                # ----------------------------------------------------
                self.log("[Step 4] Navigating to Section 6...")
                t6_x, t6_y = config.TAB_COORDINATES[6]
                self._click(t6_x, t6_y, delay_after=0.5)

                self.log(f"[Step 4] Waiting {config.SECTION_LOAD_WAIT}s for Section 6 to fully load...")
                self._wait_with_countdown(config.SECTION_LOAD_WAIT, label="Sec 6 Loading")

                self.log("[Step 4] Clicking Reset button...")
                self._click(rst_x, rst_y, delay_after=1.2)

                self.log(f"[Step 4] Selecting questions: {config.SEC6_ANSWERS_TO_CHECK}...")
                for opt_num in config.SEC6_ANSWERS_TO_CHECK:
                    if opt_num in config.SEC6_CHECKBOX_OPTIONS:
                        cx, cy = config.SEC6_CHECKBOX_OPTIONS[opt_num]
                        self.log(f"  -> Option #{opt_num} at ({cx}, {cy})...")
                        self._click(cx, cy, delay_after=0.35)

                self.log("[Step 4] Clicking Check button...")
                self._click(chk_x, chk_y, delay_after=3.0)

                nx, ny = config.MODAL_NO_BUTTON
                self.log(f"[Step 4] Clicking ({nx}, {ny}) and waiting 3s before next cycle...")
                self._click(nx, ny, delay_after=3.0)

                self.log(f"=== Cycle #{self.cycle_count} Completed! Repeating from Section 3 ===")
                self._safe_sleep(1.0)

        except KeyboardInterrupt:
            self.log("[!] Stopped by user.")
        except pyautogui.FailSafeException:
            self.log("[!] PyAutoGUI FailSafe triggered (mouse in screen corner) - Stopped!")
        except Exception as e:
            self.log(f"[!] Error occurred: {e}")
        finally:
            self.is_running = False
            self.is_paused = False
            self.log("Automation is idle.")


def run_cli():
    """Run CLI mode with keyboard hotkeys."""
    print("=" * 60)
    print(" BURLINGTON ENGLISH AUTO CLICKER & MOVER (CLI MODE)")
    print("=" * 60)
    print("Settings:")
    print(f"  Section Load Delay : {config.SECTION_LOAD_WAIT}s per section")
    print(f"  Sec 3 Play Button  : ({config.SEC3_PLAY_BUTTON[0]}, {config.SEC3_PLAY_BUTTON[1]})")
    print(f"  Sec 3 Audio Wait   : {config.SEC3_WAIT_SECONDS}s (1:15m)")
    print(f"  Sec 5 Scroll Drag  : {config.SEC5_SCROLLBAR_START} -> {config.SEC5_SCROLLBAR_END}")
    print("Hotkeys:")
    print("  [F6]  : Start / Resume Automation")
    print("  [F7]  : Pause Automation")
    print("  [F8]  : Record Play Button Coordinate (hover mouse & press F8)")
    print("  [Esc] : Stop and Exit")
    print("  Fail-safe: Slam mouse into top-left corner anytime to abort")
    print("=" * 60)

    engine = AutoClickerEngine()

    try:
        import keyboard

        def on_f6():
            if not engine.is_running:
                print("\n[Hotkey] Starting automation...")
                engine.start()
            elif engine.is_paused:
                print("\n[Hotkey] Resuming automation...")
                engine.pause()

        def on_f7():
            if engine.is_running:
                print("\n[Hotkey] Pausing/Toggling automation...")
                engine.pause()

        def on_f8():
            pos = pyautogui.position()
            config.SEC3_PLAY_BUTTON = [pos.x, pos.y]
            config.save_user_config(play_btn=pos)
            print(f"\n[Calibrate] Section 3 Play Button updated to: ({pos.x}, {pos.y}) and saved!")

        keyboard.add_hotkey("f6", on_f6)
        keyboard.add_hotkey("f7", on_f7)
        keyboard.add_hotkey("f8", on_f8)

        print("\nReady! Switch to BurlingtonEnglish and press [F6] to start...")

        keyboard.wait("esc")
        engine.stop()
        print("\nExited.")

    except ImportError:
        print("[!] 'keyboard' module not available. Starting engine directly with 5s countdown...")
        time.sleep(5)
        engine.start()
        try:
            while engine.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            engine.stop()


if __name__ == "__main__":
    run_cli()
