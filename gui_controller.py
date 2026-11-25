"""
BurlingtonEnglish Auto Clicker & Mover - Modern Graphical Dashboard.
Provides Start/Pause/Stop, live coordinate tracking, countdown timer,
settings customization, and visual action logs.
"""

import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui

import config
from auto_clicker import AutoClickerEngine

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BurlingtonEnglish Automation - Clicker & Mover")
        self.root.geometry("660x760")
        self.root.minsize(600, 640)
        self.root.configure(bg="#1e1e2e")

        self.engine = AutoClickerEngine(
            status_callback=self.on_log,
            countdown_callback=self.on_countdown
        )

        self._setup_style()
        self._build_ui()
        self._setup_hotkeys()
        self._start_mouse_tracker()

    def _setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def _build_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#21222c", pady=10)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="⚡ BurlingtonEnglish Automation",
            font=("Segoe UI", 16, "bold"),
            bg="#21222c",
            fg="#50fa7b",
        )
        title_lbl.pack()

        subtitle_lbl = tk.Label(
            header_frame,
            text="Loop: 3 (Play 1:15m) ➔ 4 (Scroll) ➔ 5 (Drag & Check) ➔ 6 (Check) | 10s Load Delays",
            font=("Segoe UI", 9),
            bg="#21222c",
            fg="#bd93f9",
        )
        subtitle_lbl.pack(pady=2)

        # Mouse position bar
        self.pos_frame = tk.Frame(self.root, bg="#282a36", pady=6)
        self.pos_frame.pack(fill="x", padx=15, pady=8)

        self.pos_lbl = tk.Label(
            self.pos_frame,
            text="Mouse: X: ---- | Y: ----",
            font=("Consolas", 11, "bold"),
            bg="#282a36",
            fg="#8be9fd",
        )
        self.pos_lbl.pack(side="left", padx=15)

        self.calibrate_btn = tk.Button(
            self.pos_frame,
            text="🎯 Set Play Button (F8)",
            font=("Segoe UI", 9, "bold"),
            bg="#ffb86c",
            fg="#282a36",
            activebackground="#ffb86c",
            relief="flat",
            padx=10,
            command=self.calibrate_play_button,
        )
        self.calibrate_btn.pack(side="right", padx=15)

        # Status & Countdown Card
        status_card = tk.Frame(self.root, bg="#282a36", padx=15, pady=10)
        status_card.pack(fill="x", padx=15, pady=5)

        status_header = tk.Label(
            status_card,
            text="Status:",
            font=("Segoe UI", 10, "bold"),
            bg="#282a36",
            fg="#f8f8f2",
        )
        status_header.grid(row=0, column=0, sticky="w")

        self.status_display = tk.Label(
            status_card,
            text="IDLE (Press Start or F6)",
            font=("Segoe UI", 11, "bold"),
            bg="#282a36",
            fg="#8be9fd",
        )
        self.status_display.grid(row=0, column=1, sticky="w", padx=10)

        self.timer_lbl = tk.Label(
            status_card,
            text="Timer: --:--",
            font=("Consolas", 11, "bold"),
            bg="#282a36",
            fg="#50fa7b",
        )
        self.timer_lbl.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        self.progress_bar = ttk.Progressbar(status_card, mode="determinate", length=400)
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        status_card.columnconfigure(1, weight=1)

        # Control Buttons
        btn_frame = tk.Frame(self.root, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=15, pady=8)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start (F6)",
            font=("Segoe UI", 11, "bold"),
            bg="#50fa7b",
            fg="#1e1e2e",
            activebackground="#50fa7b",
            relief="flat",
            padx=15,
            pady=8,
            command=self.start_automation,
        )
        self.start_btn.pack(side="left", expand=True, fill="x", padx=4)

        self.pause_btn = tk.Button(
            btn_frame,
            text="⏸ Pause (F7)",
            font=("Segoe UI", 11, "bold"),
            bg="#ffb86c",
            fg="#1e1e2e",
            activebackground="#ffb86c",
            relief="flat",
            padx=15,
            pady=8,
            command=self.pause_automation,
        )
        self.pause_btn.pack(side="left", expand=True, fill="x", padx=4)

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Stop",
            font=("Segoe UI", 11, "bold"),
            bg="#ff5555",
            fg="#f8f8f2",
            activebackground="#ff5555",
            relief="flat",
            padx=15,
            pady=8,
            command=self.stop_automation,
        )
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=4)

        # Quick Settings Frame
        settings_frame = tk.LabelFrame(
            self.root,
            text=" Settings ",
            font=("Segoe UI", 9, "bold"),
            bg="#282a36",
            fg="#f8f8f2",
            padx=10,
            pady=6,
        )
        settings_frame.pack(fill="x", padx=15, pady=6)

        # Section Load Wait
        tk.Label(settings_frame, text="Load Delay (sec):", bg="#282a36", fg="#f8f8f2").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.load_wait_entry = tk.Entry(settings_frame, width=6, font=("Consolas", 10))
        self.load_wait_entry.insert(0, str(config.SECTION_LOAD_WAIT))
        self.load_wait_entry.grid(row=0, column=1, sticky="w", padx=6)

        # Section 3 Wait duration
        tk.Label(settings_frame, text="Sec 3 Audio (sec):", bg="#282a36", fg="#f8f8f2").grid(
            row=0, column=2, sticky="w", pady=2, padx=(10, 0)
        )
        self.wait_entry = tk.Entry(settings_frame, width=6, font=("Consolas", 10))
        self.wait_entry.insert(0, str(config.SEC3_WAIT_SECONDS))
        self.wait_entry.grid(row=0, column=3, sticky="w", padx=6)

        # Play button coords
        tk.Label(settings_frame, text="Play Button:", bg="#282a36", fg="#f8f8f2").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.play_coords_lbl = tk.Label(
            settings_frame,
            text=f"({config.SEC3_PLAY_BUTTON[0]}, {config.SEC3_PLAY_BUTTON[1]})",
            bg="#282a36",
            fg="#50fa7b",
            font=("Consolas", 10, "bold"),
        )
        self.play_coords_lbl.grid(row=1, column=1, sticky="w", padx=6)

        # Section 6 answers
        tk.Label(settings_frame, text="Sec 6 Options:", bg="#282a36", fg="#f8f8f2").grid(
            row=1, column=2, sticky="w", pady=2, padx=(10, 0)
        )
        self.sec6_entry = tk.Entry(settings_frame, width=12, font=("Consolas", 10))
        self.sec6_entry.insert(0, ",".join(map(str, config.SEC6_ANSWERS_TO_CHECK)))
        self.sec6_entry.grid(row=1, column=3, sticky="w", padx=6)

        self.apply_btn = tk.Button(
            settings_frame,
            text="Save Settings",
            bg="#6272a4",
            fg="#f8f8f2",
            relief="flat",
            command=self.save_settings,
        )
        self.apply_btn.grid(row=1, column=4, sticky="e", padx=6)

        # Live Log Frame
        log_frame = tk.Frame(self.root, bg="#1e1e2e")
        log_frame.pack(fill="both", expand=True, padx=15, pady=8)

        log_lbl = tk.Label(
            log_frame,
            text="Activity Log:",
            font=("Segoe UI", 9, "bold"),
            bg="#1e1e2e",
            fg="#f8f8f2",
        )
        log_lbl.pack(anchor="w")

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            bg="#181825",
            fg="#f8f8f2",
            insertbackground="#f8f8f2",
            font=("Consolas", 9),
            height=12,
            relief="flat",
            padx=8,
            pady=8,
        )
        self.log_text.pack(fill="both", expand=True)

        footer_lbl = tk.Label(
            self.root,
            text="Emergency Stop: Move mouse to ANY screen corner | Esc in CLI",
            font=("Segoe UI", 8),
            bg="#1e1e2e",
            fg="#6272a4",
        )
        footer_lbl.pack(pady=4)

    def _setup_hotkeys(self):
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey("f6", lambda: self.root.after(0, self.start_automation))
                keyboard.add_hotkey("f7", lambda: self.root.after(0, self.pause_automation))
                keyboard.add_hotkey("f8", lambda: self.root.after(0, self.calibrate_play_button))
            except Exception:
                pass

    def _start_mouse_tracker(self):
        def update_mouse():
            try:
                pos = pyautogui.position()
                self.pos_lbl.config(text=f"Mouse: X: {pos.x:4d} | Y: {pos.y:4d}")
            except Exception:
                pass
            self.root.after(100, update_mouse)

        update_mouse()

    def on_log(self, msg):
        def _append():
            self.status_display.config(text=msg[:45] + ("..." if len(msg) > 45 else ""))
            self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see("end")

        self.root.after(0, _append)

    def on_countdown(self, remaining, total, label="Timer"):
        def _update():
            mins, secs = divmod(remaining, 60)
            self.timer_lbl.config(text=f"{label}: {mins:02d}:{secs:02d} remaining")
            progress = ((total - remaining) / total) * 100 if total > 0 else 0
            self.progress_bar["value"] = progress

        self.root.after(0, _update)

    def start_automation(self):
        if not self.engine.is_running:
            self.apply_settings()
            self.on_log("Starting automation in 3 seconds... switch to BurlingtonEnglish!")
            threading.Thread(target=self._delayed_start, daemon=True).start()
        elif self.engine.is_paused:
            self.engine.pause()

    def _delayed_start(self):
        for i in range(3, 0, -1):
            self.on_log(f"Starting in {i}s... Switch window now!")
            time.sleep(1)
        self.engine.start()

    def pause_automation(self):
        if self.engine.is_running:
            self.engine.pause()

    def stop_automation(self):
        if self.engine.is_running:
            self.engine.stop()
            self.timer_lbl.config(text="Timer: Stopped")
            self.progress_bar["value"] = 0

    def calibrate_play_button(self):
        pos = pyautogui.position()
        config.SEC3_PLAY_BUTTON = [pos.x, pos.y]
        config.save_user_config(play_btn=pos)
        self.play_coords_lbl.config(text=f"({pos.x}, {pos.y})")
        self.on_log(f"🎯 Play Button set to ({pos.x}, {pos.y}) and saved!")

    def save_settings(self):
        self.apply_settings()
        config.save_user_config(
            play_btn=config.SEC3_PLAY_BUTTON,
            sec6_answers=config.SEC6_ANSWERS_TO_CHECK,
            wait_sec=config.SEC3_WAIT_SECONDS,
            load_wait=config.SECTION_LOAD_WAIT,
        )
        self.on_log("Settings saved successfully!")

    def apply_settings(self):
        try:
            val = int(self.wait_entry.get().strip())
            config.SEC3_WAIT_SECONDS = max(1, val)
        except ValueError:
            pass

        try:
            l_val = int(self.load_wait_entry.get().strip())
            config.SECTION_LOAD_WAIT = max(1, l_val)
        except ValueError:
            pass

        try:
            raw = self.sec6_entry.get().strip()
            opts = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
            if opts:
                config.SEC6_ANSWERS_TO_CHECK = opts
        except Exception:
            pass


def main():
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
