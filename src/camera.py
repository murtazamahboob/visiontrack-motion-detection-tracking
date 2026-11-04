"""Frame sources: synthetic frames for tests/demo, optional live camera.

The synthetic generator is the default because it needs no hardware.
The live generator is a thin adapter: it imports cv2 only when called,
so importing this module never fails on a machine without OpenCV.
"""
from __future__ import annotations

import numpy as np


def synthetic_frames(width=120, height=80, count=30, start=(10, 30), step=(3, 0), size=12):
    """Yield grayscale frames with one bright square moving across them."""
    x, y = start
    for _ in range(count):
        frame = np.zeros((height, width), dtype=np.uint8)
        x0, y0 = max(0, int(x)), max(0, int(y))
        frame[y0:y0 + size, x0:x0 + size] = 255
        yield frame
        x += step[0]
        y += step[1]


def blank_frame(width=120, height=80):
    return np.zeros((height, width), dtype=np.uint8)


def live_frames(source=0):
    """Yield frames from a camera. Requires opencv-python; raises otherwise."""
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "Live camera needs opencv-python (pip install opencv-python). "
            "Use synthetic_frames() without a camera."
        ) from exc
    cap = cv2.VideoCapture(source)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
    finally:
        cap.release()
