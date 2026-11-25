"""
Visual pill detector and modal guard for BurlingtonEnglish Section 5 & 6.
Detects the randomized order of the 4 draggable word pills on screen
using normalized 2D cross-correlation + 1-to-1 optimal assignment.
"""

import os
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scipy.optimize import linear_sum_assignment
from scipy.signal import correlate2d

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
PILL_NAMES = ("style", "technique", "opinion", "interpretation")


def _load_templates():
    """Load grayscale text-interior templates for the 4 Section 5 pills."""
    templates = {}
    for name in PILL_NAMES:
        path = os.path.join(ASSETS_DIR, f"tpl_{name}.png")
        arr = np.array(Image.open(path).convert("L"), dtype=np.float64)
        arr -= arr.mean()
        std = arr.std()
        if std > 0:
            arr /= std
        templates[name] = arr
    return templates


_TEMPLATES = None


def _get_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = _load_templates()
    return _TEMPLATES


def detect_pills_from_image(img):
    """
    Detect the 4 Section 5 word pills in a 1920x1080 screenshot.
    Returns a tuple (mapping, scores_info) where mapping is:
        {
            'style': (cx, cy),
            'technique': (cx, cy),
            'opinion': (cx, cy),
            'interpretation': (cx, cy),
        }
    """
    templates = _get_templates()

    # Dynamically locate the horizontal pill bar anywhere in y=340..460
    scan_y1, scan_y2 = 340, 460
    scan_crop = img.crop((50, scan_y1, 1850, scan_y2))
    scan_arr = np.array(scan_crop)
    # Blue pill background: low R, medium G, high B
    blue_mask = (scan_arr[:, :, 0] < 175) & (scan_arr[:, :, 1] > 95) & (scan_arr[:, :, 2] > 170)
    y_proj = blue_mask.sum(axis=1) > 400
    y_lbl, y_num = label(y_proj)
    pill_y1, pill_y2 = 371, 401  # default shifted band
    best_h = 0
    for i in range(1, y_num + 1):
        ys = np.where(y_lbl == i)[0] + scan_y1
        if len(ys) > best_h:
            best_h = len(ys)
            pill_y1 = max(0, int(ys.min()) - 10)
            pill_y2 = int(ys.max()) + 4
    if pill_y2 - pill_y1 < 26:
        mid_y = (pill_y1 + pill_y2) // 2
        pill_y1, pill_y2 = mid_y - 18, mid_y + 18

    crop = img.crop((50, pill_y1, 1850, pill_y2))
    arr = np.array(crop)
    non_white = (arr[:, :, 0] < 230) | (arr[:, :, 1] < 230) | (arr[:, :, 2] < 230)
    x_proj = non_white.any(axis=0)
    lbl, num = label(x_proj)

    pills = []
    cy = (pill_y1 + pill_y2) // 2
    for i in range(1, num + 1):
        pts = np.where(lbl == i)[0] + 50
        if pts.max() - pts.min() > 100:
            cx = int((pts.min() + pts.max()) / 2)
            pills.append((int(pts.min()), int(pts.max()), cx, cy))

    if len(pills) != 4:
        raise RuntimeError(f"Expected 4 pills in Section 5 bar, found {len(pills)}")

    # Compute 4x4 normalized cross-correlation score matrix (pills x templates)
    score_matrix = np.zeros((4, 4), dtype=np.float64)
    for p_idx, (x1, x2, _, _) in enumerate(pills):
        pill_strip = np.array(img.crop((x1, pill_y1, x2, pill_y2)).convert("L"), dtype=np.float64)
        pill_strip -= pill_strip.mean()
        p_std = pill_strip.std()
        if p_std > 0:
            pill_strip /= p_std

        for t_idx, name in enumerate(PILL_NAMES):
            tpl = templates[name]
            corr = correlate2d(pill_strip, tpl, mode="valid")
            score_matrix[p_idx, t_idx] = corr.max() / tpl.size

    # Optimal 1-to-1 assignment guarantees every pill is mapped uniquely
    row_ind, col_ind = linear_sum_assignment(-score_matrix)

    mapping = {}
    info = []
    for r, c in zip(row_ind, col_ind):
        name = PILL_NAMES[c]
        _, _, cx, cy = pills[r]
        mapping[name] = (cx, cy)
        info.append(f"{name}@({cx},{cy})={score_matrix[r, c]:.2f}")

    return mapping, info


def is_modal_popup_visible(img):
    """
    Detect if the 'Do you want to correct yourself?' modal is visible.
    Checks both the shifted (-36px) and original modal coordinates.
    """
    for dy in (-36, 0):
        r1, g1, b1 = img.getpixel((966, 390 + dy))[:3]
        r2, g2, b2 = img.getpixel((1280, 590 + dy))[:3]
        header_is_blue = r1 < 80 and 90 < g1 < 160 and b1 > 165
        no_btn_is_blue = r2 < 80 and 90 < g2 < 160 and b2 > 165
        if header_is_blue and no_btn_is_blue:
            return True
    return False
