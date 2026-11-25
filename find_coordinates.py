"""
Interactive Mouse Coordinate & RGB Color Inspector.
Hover your mouse over any UI element to see its coordinates in real time.
Press Ctrl+C to exit.
"""

import sys
import time
import ctypes
import pyautogui

# Set DPI awareness for 100% accurate coordinates on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def main():
    print("=" * 60)
    print(" 🔍 MOUSE COORDINATE INSPECTOR")
    print("=" * 60)
    print("Move your mouse over buttons, tabs, or elements.")
    print("The X and Y coordinates will update below in real-time.")
    print("Press Ctrl+C in this window when done.\n")

    try:
        while True:
            x, y = pyautogui.position()
            pos_str = f"X: {x:4d} | Y: {y:4d}"
            sys.stdout.write(f"\r  Current Mouse Position -> {pos_str}  ")
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\nFinished inspector.")


if __name__ == "__main__":
    main()
