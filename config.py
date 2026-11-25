"""
Configuration settings and coordinates for BurlingtonEnglish Auto Clicker & Mover.
Pre-calibrated with exact coordinates from user screen:
- Section 3 Play Button: (43, 442)
- Section 4 Scrollbar Drag: (1531, 500) -> (1531, 750)
- Section 5 Scrollbar Drag: (1588, 584) -> (1590, 649)
- Section 5 Drop Slots: (1233, 607), (1238, 698), (1233, 793), (1236, 888)
- 10-second wait on every section transition to let content fully load.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Screen middle position
SCREEN_MID = (960, 540)

# Section Load Delay (Wait 10 seconds after clicking each tab so it loads)
SECTION_LOAD_WAIT = 10

# Navigation Bar Tabs (Y = 292, shifted -36 from 328)
TAB_COORDINATES = {
    1: (580, 292),
    2: (660, 292),
    3: (745, 292),
    4: (825, 292),
    5: (905, 292),
    6: (985, 292),
    7: (1065, 292),
    8: (1145, 292),
    9: (1225, 292),
}

# --- Section 3 ---
# Play button on top left (Y in 395..405 range)
SEC3_PLAY_BUTTON = [43, 400]
SEC3_WAIT_SECONDS = 75  # 1 minute 15 seconds after pressing play

# --- Section 4 ---
# Scrollbar thumb drag to scroll down the card reliably (shifted -36)
SEC4_SCROLLBAR_START = [1531, 464]
SEC4_SCROLLBAR_END = [1531, 714]
SEC4_WAIT_SECONDS = 3

# --- Section 5 ---
# Side scrollbar thumb drag (shifted -36 from 584 -> 649)
SEC5_SCROLLBAR_START = [1588, 548]
SEC5_SCROLLBAR_END = [1590, 613]
SEC5_SCROLL_DELAY = 1.0

# Bottom Right Action Buttons (exact user-verified coordinates)
RESET_BUTTON = [1876, 986]
CHECK_BUTTON = [1785, 987]
MODAL_NO_BUTTON = [1281, 557]  # "No" button on "Do you want to correct yourself?" popup

# Section 5: Word Pills at top (fallback coordinates if visual detection fails)
# 0: Pill 1 ("Information about the artist's style")
# 1: Pill 2 ("A description of the artist's technique")
# 2: Pill 3 ("The critic's interpretation of the work")
# 3: Pill 4 ("The critic's overall opinion of the event")
SEC5_PILLS = [
    [306, 389],   # Pill 1
    [720, 389],   # Pill 2
    [1137, 388],  # Pill 3
    [1571, 392],  # Pill 4
]

# Section 5: Target Drop Slots (after scroll, Slot 1 adjusted +3px more down)
# Slot 1: (1225, 582) -> style
# Slot 2: (1230, 675) -> technique
# Slot 3: (1217, 769) -> opinion
# Slot 4: (1225, 866) -> interpretation
SEC5_SLOT_TARGETS = {
    "style": [1225, 582],
    "technique": [1230, 675],
    "opinion": [1217, 769],
    "interpretation": [1225, 866],
}

SEC5_SLOTS = [
    [1225, 582],  # Slot 1
    [1230, 675],  # Slot 2
    [1217, 769],  # Slot 3
    [1225, 866],  # Slot 4
]

# Drag-and-drop pairings: [pill_index, slot_index]
# Pill 1 -> Slot 1
# Pill 2 -> Slot 2
# Pill 4 -> Slot 3
# Pill 3 -> Slot 4
SEC5_DRAG_PAIRS = [
    [0, 0],  # Pill 1 to Slot 1
    [1, 1],  # Pill 2 to Slot 2
    [3, 2],  # Pill 4 to Slot 3
    [2, 3],  # Pill 3 to Slot 4
]

# --- Section 6 ---
# 9 Multiple choice options (radio / checkbox circles at x=1068, shifted -36)
SEC6_CHECKBOX_OPTIONS = {
    1: [1068, 473],  # Name of the artist
    2: [1068, 511],  # Name of the exhibit
    3: [1068, 548],  # Where you can see the exhibit
    4: [1068, 586],  # The dates of the exhibit
    5: [1068, 623],  # Biographical information about the artist
    6: [1068, 661],  # Information about the artist's style
    7: [1068, 698],  # A description of pieces in the collection
    8: [1068, 736],  # An opinion of the work
    9: [1068, 773],  # An interpretation of the work
}

# Checkboxes to click in Section 6
SEC6_ANSWERS_TO_CHECK = [1, 6, 7, 8]

# Action delays (in seconds)
CLICK_DELAY = 0.4
TRANSITION_DELAY = 1.0
DRAG_DURATION = 0.5


def save_user_config(play_btn=None, sec6_answers=None, wait_sec=None, load_wait=None):
    """Save persistent changes to config.json."""
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    if play_btn is not None:
        data["SEC3_PLAY_BUTTON"] = list(play_btn)
    if sec6_answers is not None:
        data["SEC6_ANSWERS_TO_CHECK"] = list(sec6_answers)
    if wait_sec is not None:
        data["SEC3_WAIT_SECONDS"] = int(wait_sec)
    if load_wait is not None:
        data["SECTION_LOAD_WAIT"] = int(load_wait)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_user_config():
    """Load overrides from config.json if present."""
    global SEC3_PLAY_BUTTON, SEC6_ANSWERS_TO_CHECK, SEC3_WAIT_SECONDS, SECTION_LOAD_WAIT
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "SEC3_PLAY_BUTTON" in data:
                    SEC3_PLAY_BUTTON = data["SEC3_PLAY_BUTTON"]
                if "SEC6_ANSWERS_TO_CHECK" in data:
                    SEC6_ANSWERS_TO_CHECK = data["SEC6_ANSWERS_TO_CHECK"]
                if "SEC3_WAIT_SECONDS" in data:
                    SEC3_WAIT_SECONDS = data["SEC3_WAIT_SECONDS"]
                if "SECTION_LOAD_WAIT" in data:
                    SECTION_LOAD_WAIT = data["SECTION_LOAD_WAIT"]
        except Exception:
            pass


load_user_config()
