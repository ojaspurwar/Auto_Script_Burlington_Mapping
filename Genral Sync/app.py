"""
Genral Sync - Visual Sequence Builder & Auto Clicker GUI
Create, customize, save, and share mouse click/drag/wait/scroll sequences
for any screen resolution, any module, or any app — without typing coordinates.
"""

import json
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyautogui

from engine import SequenceEngine, get_screen_size

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    from pynput import mouse as pynput_mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(APP_DIR, "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)


def format_step(idx, step):
    """Return human-readable summary for the sequence list."""
    stype = step.get("type", "click")
    label = step.get("label", "").strip()
    tag = f"  [{label}]" if label else ""

    if stype == "click":
        clicks = step.get("clicks", 1)
        kind = "Double-Click" if clicks == 2 else "Click"
        return f"{idx + 1}. {kind} ({step['x']}, {step['y']}){tag}"
    if stype == "wait":
        return f"{idx + 1}. Wait {step['seconds']}s{tag}"
    if stype == "drag":
        return f"{idx + 1}. Drag ({step['x1']}, {step['y1']}) ➔ ({step['x2']}, {step['y2']}){tag}"
    if stype == "scroll":
        direction = "Up" if int(step["amount"]) > 0 else "Down"
        return f"{idx + 1}. Scroll {direction} ({step['amount']}) at ({step['x']}, {step['y']}){tag}"
    if stype == "move":
        return f"{idx + 1}. Move to ({step['x']}, {step['y']}){tag}"
    return f"{idx + 1}. {stype}{tag}"


class GenralSyncApp:
    def __init__(self, root):
        self.root = root
        w, h = get_screen_size()
        self.root.title(f"Genral Sync — Universal Sequence Clicker ({w}x{h})")
        self.root.geometry("920x680")
        self.root.minsize(820, 600)
        self.root.configure(bg="#181825")

        self.steps = []
        self.capture_target = None  # "primary" or "secondary"
        self.triple_click_armed = False
        self._click_times = []
        self._mouse_listener = None

        self.engine = SequenceEngine(
            status_cb=self._on_status,
            step_cb=self._on_step_highlight,
            countdown_cb=self._on_countdown,
            done_cb=self._on_done,
        )

        self._build_ui(w, h)
        self._setup_hotkeys()
        self._start_mouse_tracker()
        self._load_default_profile()

    # ------------------------------------------------------------------ UI
    def _build_ui(self, screen_w, screen_h):
        style = ttk.Style()
        style.theme_use("clam")

        # Top header
        top = tk.Frame(self.root, bg="#11111b", pady=8, padx=14)
        top.pack(fill="x")

        tk.Label(
            top,
            text="Genral Sync",
            font=("Segoe UI", 16, "bold"),
            bg="#11111b",
            fg="#a6e3a1",
        ).pack(side="left")

        tk.Label(
            top,
            text=f"Screen: {screen_w}x{screen_h}",
            font=("Consolas", 10),
            bg="#11111b",
            fg="#94e2d5",
        ).pack(side="left", padx=16)

        self.mouse_lbl = tk.Label(
            top,
            text="Mouse: (0, 0)",
            font=("Consolas", 11, "bold"),
            bg="#11111b",
            fg="#89dceb",
        )
        self.mouse_lbl.pack(side="right")

        # Capture hint banner
        self.capture_banner = tk.Label(
            self.root,
            text="Tip: Hover over any button on screen & press [F8] to capture coordinates (or use 3-Click Capture)!",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg="#f9e2af",
            pady=5,
        )
        self.capture_banner.pack(fill="x")

        # Main split body
        body = tk.Frame(self.root, bg="#181825", padx=12, pady=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # LEFT: Sequence List + Reorder + Profiles
        left = tk.Frame(body, bg="#1e1e2e", padx=10, pady=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        list_hdr = tk.Frame(left, bg="#1e1e2e")
        list_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        tk.Label(
            list_hdr,
            text="Step Sequence (Runs Top ➔ Bottom)",
            font=("Segoe UI", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4",
        ).pack(side="left")

        tk.Button(
            list_hdr, text="Save Profile", bg="#45475a", fg="#cdd6f4",
            relief="flat", padx=8, command=self.save_profile
        ).pack(side="right", padx=2)
        tk.Button(
            list_hdr, text="Load Profile", bg="#45475a", fg="#cdd6f4",
            relief="flat", padx=8, command=self.load_profile
        ).pack(side="right", padx=2)

        list_box_frame = tk.Frame(left, bg="#1e1e2e")
        list_box_frame.grid(row=1, column=0, sticky="nsew")
        list_box_frame.rowconfigure(0, weight=1)
        list_box_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_box_frame,
            bg="#11111b",
            fg="#cdd6f4",
            selectbackground="#585b70",
            selectforeground="#ffffff",
            font=("Consolas", 10),
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind("<<ListboxSelect>>", self._on_select_step)

        sb = ttk.Scrollbar(list_box_frame, orient="vertical", command=self.listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=sb.set)

        list_btns = tk.Frame(left, bg="#1e1e2e", pady=6)
        list_btns.grid(row=2, column=0, sticky="ew")
        for text, cmd in [
            ("▲ Up", self.move_up),
            ("▼ Down", self.move_down),
            ("Duplicate", self.duplicate_step),
            ("Delete", self.delete_step),
            ("Clear All", self.clear_steps),
        ]:
            tk.Button(
                list_btns, text=text, bg="#313244", fg="#cdd6f4",
                relief="flat", padx=8, pady=4, command=cmd
            ).pack(side="left", padx=3)

        # RIGHT: Step Builder Form
        right = tk.Frame(body, bg="#1e1e2e", padx=12, pady=10)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            right,
            text="Add / Edit Step",
            font=("Segoe UI", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4",
        ).pack(anchor="w", pady=(0, 8))

        # Action type selector
        type_row = tk.Frame(right, bg="#1e1e2e")
        type_row.pack(fill="x", pady=4)
        tk.Label(type_row, text="Action:", width=9, anchor="w", bg="#1e1e2e", fg="#bac2de").pack(side="left")
        self.action_var = tk.StringVar(value="click")
        self.action_combo = ttk.Combobox(
            type_row,
            textvariable=self.action_var,
            values=["click", "wait", "drag", "scroll", "move"],
            state="readonly",
            width=14,
        )
        self.action_combo.pack(side="left", fill="x", expand=True)
        self.action_combo.bind("<<ComboboxSelected>>", lambda e: self._update_form_fields())

        # Label input
        lbl_row = tk.Frame(right, bg="#1e1e2e")
        lbl_row.pack(fill="x", pady=4)
        tk.Label(lbl_row, text="Label:", width=9, anchor="w", bg="#1e1e2e", fg="#bac2de").pack(side="left")
        self.label_entry = tk.Entry(lbl_row, bg="#11111b", fg="#cdd6f4", insertbackground="#cdd6f4", relief="flat")
        self.label_entry.pack(side="left", fill="x", expand=True, ipady=3)

        # Dynamic fields container
        self.fields_frame = tk.Frame(right, bg="#1e1e2e", pady=6)
        self.fields_frame.pack(fill="x")

        # Point 1 row (Click / Move / Scroll / Drag From)
        self.p1_frame = tk.Frame(self.fields_frame, bg="#1e1e2e")
        self.p1_lbl = tk.Label(self.p1_frame, text="Point:", width=9, anchor="w", bg="#1e1e2e", fg="#bac2de")
        self.p1_lbl.pack(side="left")
        self.x1_entry = tk.Entry(self.p1_frame, width=6, bg="#11111b", fg="#89dceb", insertbackground="#cdd6f4", relief="flat")
        self.x1_entry.insert(0, "0")
        self.x1_entry.pack(side="left", padx=2, ipady=3)
        self.y1_entry = tk.Entry(self.p1_frame, width=6, bg="#11111b", fg="#89dceb", insertbackground="#cdd6f4", relief="flat")
        self.y1_entry.insert(0, "0")
        self.y1_entry.pack(side="left", padx=2, ipady=3)
        tk.Button(
            self.p1_frame, text="🎯 F8", bg="#f9e2af", fg="#11111b",
            font=("Segoe UI", 8, "bold"), relief="flat", padx=6,
            command=lambda: self._arm_capture("primary", triple=False)
        ).pack(side="left", padx=3)
        tk.Button(
            self.p1_frame, text="3-Click", bg="#fab387", fg="#11111b",
            font=("Segoe UI", 8, "bold"), relief="flat", padx=6,
            command=lambda: self._arm_capture("primary", triple=True)
        ).pack(side="left", padx=2)

        # Point 2 row (Drag To)
        self.p2_frame = tk.Frame(self.fields_frame, bg="#1e1e2e")
        tk.Label(self.p2_frame, text="Drag To:", width=9, anchor="w", bg="#1e1e2e", fg="#bac2de").pack(side="left")
        self.x2_entry = tk.Entry(self.p2_frame, width=6, bg="#11111b", fg="#a6e3a1", insertbackground="#cdd6f4", relief="flat")
        self.x2_entry.insert(0, "0")
        self.x2_entry.pack(side="left", padx=2, ipady=3)
        self.y2_entry = tk.Entry(self.p2_frame, width=6, bg="#11111b", fg="#a6e3a1", insertbackground="#cdd6f4", relief="flat")
        self.y2_entry.insert(0, "0")
        self.y2_entry.pack(side="left", padx=2, ipady=3)
        tk.Button(
            self.p2_frame, text="🎯 F8", bg="#f9e2af", fg="#11111b",
            font=("Segoe UI", 8, "bold"), relief="flat", padx=6,
            command=lambda: self._arm_capture("secondary", triple=False)
        ).pack(side="left", padx=3)
        tk.Button(
            self.p2_frame, text="3-Click", bg="#fab387", fg="#11111b",
            font=("Segoe UI", 8, "bold"), relief="flat", padx=6,
            command=lambda: self._arm_capture("secondary", triple=True)
        ).pack(side="left", padx=2)

        # Extra numeric value row (Wait seconds / Scroll amount / After delay)
        self.val_frame = tk.Frame(self.fields_frame, bg="#1e1e2e")
        self.val_lbl = tk.Label(self.val_frame, text="Seconds:", width=9, anchor="w", bg="#1e1e2e", fg="#bac2de")
        self.val_lbl.pack(side="left")
        self.val_entry = tk.Entry(self.val_frame, width=10, bg="#11111b", fg="#cdd6f4", insertbackground="#cdd6f4", relief="flat")
        self.val_entry.insert(0, "5")
        self.val_entry.pack(side="left", padx=2, ipady=3)

        # Add / Update step buttons
        act_btns = tk.Frame(right, bg="#1e1e2e", pady=8)
        act_btns.pack(fill="x")
        tk.Button(
            act_btns, text="+ Add Step", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6,
            command=self.add_step
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(
            act_btns, text="Update Selected", bg="#89b4fa", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6,
            command=self.update_selected_step
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Run Options & Controls
        run_box = tk.LabelFrame(
            right, text=" Run Controls ", bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 9, "bold"), padx=10, pady=8
        )
        run_box.pack(fill="x", pady=(10, 4))

        rep_row = tk.Frame(run_box, bg="#1e1e2e")
        rep_row.pack(fill="x", pady=(0, 6))
        tk.Label(rep_row, text="Repeat (0 = Forever):", bg="#1e1e2e", fg="#bac2de").pack(side="left")
        self.repeat_entry = tk.Entry(rep_row, width=6, bg="#11111b", fg="#cdd6f4", relief="flat")
        self.repeat_entry.insert(0, "0")
        self.repeat_entry.pack(side="left", padx=8, ipady=2)

        ctrl_row = tk.Frame(run_box, bg="#1e1e2e")
        ctrl_row.pack(fill="x")
        tk.Button(
            ctrl_row, text="▶ Start (F6)", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6,
            command=self.start_run
        ).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(
            ctrl_row, text="⏸ Pause (F7)", bg="#fab387", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6,
            command=self.pause_run
        ).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(
            ctrl_row, text="⏹ Stop", bg="#f38ba8", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6,
            command=self.stop_run
        ).pack(side="left", expand=True, fill="x", padx=2)

        # Status + Progress
        self.status_lbl = tk.Label(
            right, text="Status: Idle", font=("Segoe UI", 9, "bold"),
            bg="#1e1e2e", fg="#89dceb", anchor="w"
        )
        self.status_lbl.pack(fill="x", pady=(8, 2))
        self.timer_lbl = tk.Label(
            right, text="Timer: --:--", font=("Consolas", 10, "bold"),
            bg="#1e1e2e", fg="#a6e3a1", anchor="w"
        )
        self.timer_lbl.pack(fill="x")
        self.pbar = ttk.Progressbar(right, mode="determinate")
        self.pbar.pack(fill="x", pady=4)

        self._update_form_fields()

    def _update_form_fields(self):
        for f in (self.p1_frame, self.p2_frame, self.val_frame):
            f.pack_forget()

        stype = self.action_var.get()
        if stype in ("click", "move", "scroll"):
            self.p1_lbl.config(text="Point:")
            self.p1_frame.pack(fill="x", pady=4)
            if stype == "scroll":
                self.val_lbl.config(text="Scroll:")
                self.val_entry.delete(0, "end")
                self.val_entry.insert(0, "-300")
                self.val_frame.pack(fill="x", pady=4)
            elif stype == "click":
                self.val_lbl.config(text="After (s):")
                self.val_entry.delete(0, "end")
                self.val_entry.insert(0, "0.4")
                self.val_frame.pack(fill="x", pady=4)
        elif stype == "drag":
            self.p1_lbl.config(text="Drag From:")
            self.p1_frame.pack(fill="x", pady=4)
            self.p2_frame.pack(fill="x", pady=4)
            self.val_lbl.config(text="Speed (s):")
            self.val_entry.delete(0, "end")
            self.val_entry.insert(0, "0.5")
            self.val_frame.pack(fill="x", pady=4)
        elif stype == "wait":
            self.val_lbl.config(text="Seconds:")
            self.val_entry.delete(0, "end")
            self.val_entry.insert(0, "10")
            self.val_frame.pack(fill="x", pady=4)

    # ---------------------------------------------------- Coordinate Capture
    def _arm_capture(self, target, triple=False):
        self.capture_target = target
        if triple:
            if not PYNPUT_AVAILABLE:
                messagebox.showinfo("Use F8", "Triple-click listener unavailable; hover and press F8 instead.")
                return
            self.triple_click_armed = True
            self._click_times = []
            self.capture_banner.config(
                text=f"ARMED ({target}): Triple-click anywhere on screen to capture coordinates!",
                bg="#fab387", fg="#11111b"
            )
            self._start_triple_click_listener()
        else:
            self.triple_click_armed = False
            self.capture_banner.config(
                text=f"ARMED ({target}): Hover your mouse over the target and press [F8]!",
                bg="#f9e2af", fg="#11111b"
            )

    def _apply_captured_pos(self, x, y, target=None):
        tgt = target or self.capture_target or "primary"
        if tgt == "secondary":
            self.x2_entry.delete(0, "end")
            self.x2_entry.insert(0, str(x))
            self.y2_entry.delete(0, "end")
            self.y2_entry.insert(0, str(y))
        else:
            self.x1_entry.delete(0, "end")
            self.x1_entry.insert(0, str(x))
            self.y1_entry.delete(0, "end")
            self.y1_entry.insert(0, str(y))

        self.capture_banner.config(
            text=f"Captured ({x}, {y}) into {tgt}! Hover & press [F8] anytime to capture again.",
            bg="#313244", fg="#a6e3a1"
        )
        self.triple_click_armed = False

    def _on_f8_capture(self):
        pos = pyautogui.position()
        self._apply_captured_pos(pos.x, pos.y)

    def _start_triple_click_listener(self):
        if self._mouse_listener is not None:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass

        def on_click(x, y, button, pressed):
            if not pressed or not self.triple_click_armed:
                return
            now = time.time()
            self._click_times = [t for t in self._click_times if now - t < 0.7]
            self._click_times.append(now)
            if len(self._click_times) >= 3:
                self.triple_click_armed = False
                self._click_times = []
                self.root.after(0, lambda cx=int(x), cy=int(y): self._apply_captured_pos(cx, cy))
                return False  # Stop listener

        self._mouse_listener = pynput_mouse.Listener(on_click=on_click)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    # -------------------------------------------------------- Step List CRUD
    def _build_step_from_form(self):
        stype = self.action_var.get()
        label = self.label_entry.get().strip()
        try:
            if stype == "click":
                return {
                    "type": "click",
                    "x": int(self.x1_entry.get()),
                    "y": int(self.y1_entry.get()),
                    "after": float(self.val_entry.get() or 0.4),
                    "label": label,
                }
            if stype == "wait":
                return {
                    "type": "wait",
                    "seconds": float(self.val_entry.get() or 1),
                    "label": label,
                }
            if stype == "drag":
                return {
                    "type": "drag",
                    "x1": int(self.x1_entry.get()),
                    "y1": int(self.y1_entry.get()),
                    "x2": int(self.x2_entry.get()),
                    "y2": int(self.y2_entry.get()),
                    "duration": float(self.val_entry.get() or 0.5),
                    "label": label,
                }
            if stype == "scroll":
                return {
                    "type": "scroll",
                    "x": int(self.x1_entry.get()),
                    "y": int(self.y1_entry.get()),
                    "amount": int(self.val_entry.get() or -300),
                    "label": label,
                }
            if stype == "move":
                return {
                    "type": "move",
                    "x": int(self.x1_entry.get()),
                    "y": int(self.y1_entry.get()),
                    "label": label,
                }
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for coordinates/time.")
            return None

    def _refresh_list(self, select_idx=None):
        self.listbox.delete(0, "end")
        for i, step in enumerate(self.steps):
            self.listbox.insert("end", format_step(i, step))
        if select_idx is not None and 0 <= select_idx < len(self.steps):
            self.listbox.selection_set(select_idx)

    def add_step(self):
        step = self._build_step_from_form()
        if step is None:
            return
        self.steps.append(step)
        self._refresh_list(len(self.steps) - 1)

    def update_selected_step(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        step = self._build_step_from_form()
        if step is None:
            return
        self.steps[idx] = step
        self._refresh_list(idx)

    def _on_select_step(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        step = self.steps[sel[0]]
        self.action_var.set(step.get("type", "click"))
        self._update_form_fields()
        self.label_entry.delete(0, "end")
        self.label_entry.insert(0, step.get("label", ""))

        stype = step.get("type")
        if stype in ("click", "move", "scroll"):
            self.x1_entry.delete(0, "end")
            self.x1_entry.insert(0, str(step["x"]))
            self.y1_entry.delete(0, "end")
            self.y1_entry.insert(0, str(step["y"]))
            if stype == "scroll":
                self.val_entry.delete(0, "end")
                self.val_entry.insert(0, str(step.get("amount", -300)))
            elif stype == "click":
                self.val_entry.delete(0, "end")
                self.val_entry.insert(0, str(step.get("after", 0.4)))
        elif stype == "drag":
            self.x1_entry.delete(0, "end")
            self.x1_entry.insert(0, str(step["x1"]))
            self.y1_entry.delete(0, "end")
            self.y1_entry.insert(0, str(step["y1"]))
            self.x2_entry.delete(0, "end")
            self.x2_entry.insert(0, str(step["x2"]))
            self.y2_entry.delete(0, "end")
            self.y2_entry.insert(0, str(step["y2"]))
            self.val_entry.delete(0, "end")
            self.val_entry.insert(0, str(step.get("duration", 0.5)))
        elif stype == "wait":
            self.val_entry.delete(0, "end")
            self.val_entry.insert(0, str(step.get("seconds", 5)))

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.steps[i - 1], self.steps[i] = self.steps[i], self.steps[i - 1]
        self._refresh_list(i - 1)

    def move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.steps) - 1:
            return
        i = sel[0]
        self.steps[i + 1], self.steps[i] = self.steps[i], self.steps[i + 1]
        self._refresh_list(i + 1)

    def duplicate_step(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        i = sel[0]
        self.steps.insert(i + 1, dict(self.steps[i]))
        self._refresh_list(i + 1)

    def delete_step(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        i = sel[0]
        del self.steps[i]
        self._refresh_list(min(i, len(self.steps) - 1))

    def clear_steps(self):
        if self.steps and messagebox.askyesno("Clear All", "Remove all steps from the sequence?"):
            self.steps = []
            self._refresh_list()

    # -------------------------------------------------------------- Profiles
    def save_profile(self):
        path = filedialog.asksaveasfilename(
            initialdir=PROFILES_DIR,
            defaultextension=".json",
            filetypes=[("JSON Profile", "*.json")],
            title="Save Sequence Profile",
        )
        if not path:
            return
        w, h = get_screen_size()
        payload = {"screen": f"{w}x{h}", "steps": self.steps}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self._on_status(f"Saved profile: {os.path.basename(path)}")

    def load_profile(self):
        path = filedialog.askopenfilename(
            initialdir=PROFILES_DIR,
            filetypes=[("JSON Profile", "*.json")],
            title="Load Sequence Profile",
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.steps = data.get("steps", data) if isinstance(data, dict) else data
        self._refresh_list(0 if self.steps else None)
        self._on_status(f"Loaded {len(self.steps)} steps from {os.path.basename(path)}")

    def _load_default_profile(self):
        sample = os.path.join(PROFILES_DIR, "sample_profile.json")
        if os.path.exists(sample):
            try:
                with open(sample, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.steps = data.get("steps", [])
                self._refresh_list()
            except Exception:
                pass

    # ----------------------------------------------------------- Run & State
    def start_run(self):
        if self.engine.is_running:
            if self.engine.is_paused:
                self.engine.pause()
            return
        if not self.steps:
            messagebox.showwarning("No Steps", "Add at least one step to the sequence first!")
            return
        try:
            rep = int(self.repeat_entry.get().strip() or 0)
        except ValueError:
            rep = 0

        def delayed():
            for s in (3, 2, 1):
                self._on_status(f"Starting in {s}s... Switch to target window!")
                time.sleep(1)
            self.engine.start(self.steps, repeat_count=rep)

        threading.Thread(target=delayed, daemon=True).start()

    def pause_run(self):
        if self.engine.is_running:
            self.engine.pause()

    def stop_run(self):
        if self.engine.is_running:
            self.engine.stop()

    def _on_status(self, msg):
        self.root.after(0, lambda: self.status_lbl.config(text=f"Status: {msg}"))

    def _on_step_highlight(self, idx, cycle):
        def _upd():
            self.listbox.selection_clear(0, "end")
            if 0 <= idx < len(self.steps):
                self.listbox.selection_set(idx)
                self.listbox.see(idx)
        self.root.after(0, _upd)

    def _on_countdown(self, rem, tot, label):
        def _upd():
            m, s = divmod(rem, 60)
            self.timer_lbl.config(text=f"{label}: {m:02d}:{s:02d} left")
            self.pbar["value"] = ((tot - rem) / tot * 100) if tot > 0 else 0
        self.root.after(0, _upd)

    def _on_done(self):
        def _upd():
            self.timer_lbl.config(text="Timer: --:--")
            self.pbar["value"] = 0
        self.root.after(0, _upd)

    def _setup_hotkeys(self):
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey("f6", lambda: self.root.after(0, self.start_run))
                keyboard.add_hotkey("f7", lambda: self.root.after(0, self.pause_run))
                keyboard.add_hotkey("f8", lambda: self.root.after(0, self._on_f8_capture))
                keyboard.add_hotkey("esc", lambda: self.root.after(0, self.stop_run))
            except Exception:
                pass

    def _start_mouse_tracker(self):
        def tick():
            try:
                p = pyautogui.position()
                self.mouse_lbl.config(text=f"Mouse: ({p.x}, {p.y})")
            except Exception:
                pass
            self.root.after(100, tick)
        tick()


def main():
    root = tk.Tk()
    GenralSyncApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
