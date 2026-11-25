# Genral Sync — Universal Sequence Clicker

A resolution-independent, zero-typing mouse automation builder. Works on **any Windows screen resolution**, **any DPI scaling**, and **any website or app** (BurlingtonEnglish, courses, forms, etc.).

---

## How to Run (For You or Your Friend)

1. Copy the **`Genral Sync`** folder anywhere on your PC.
2. Double-click **`run.bat`** (it automatically installs `pyautogui`, `keyboard`, and `pynput` on first run if needed).

---

## How to Build Your Own Sequence (Zero Typing!)

You never have to manually figure out `(X, Y)` coordinates:

1. **Choose an Action** on the right panel:
   - **`click`** — Click a button/tab/option at `(x, y)`
   - **`wait`** — Pause for `N` seconds with a live countdown (e.g., `10` for page load, `75` for 1:15 audio)
   - **`drag`** — Drag from `(x1, y1)` to `(x2, y2)` (great for dragging words OR dragging a scrollbar thumb)
   - **`scroll`** — Scroll mouse wheel up (`+`) or down (`-`) at `(x, y)`
   - **`move`** — Move mouse to `(x, y)` without clicking
2. **Capture Coordinates Instantly** (two ways):
   - **Option A — `F8` Hover Shortcut (Recommended)**: Click **`🎯 F8`**, move your mouse over the button on your screen, and press **`F8`**.
   - **Option B — `3-Click` Capture**: Click **`3-Click`**, then **triple-click** on the target spot on your screen.
3. Click **`+ Add Step`**.
4. Reorder steps anytime using **`▲ Up`**, **`▼ Down`**, **`Duplicate`**, or **`Delete`**.
5. Click **`Save Profile`** to save your setup as a `.json` file in `profiles/` (you can share `.json` profiles with friends who have the same screen resolution!).

---

## Controls & Safety

| Key / Action | What It Does |
| :--- | :--- |
| **`F6`** | Start / Resume sequence |
| **`F7`** | Pause / Resume |
| **`F8`** | Capture current mouse `(X, Y)` |
| **`Esc`** | Stop running sequence |
| **Screen Corner** | Move mouse to any corner to emergency-abort immediately |
