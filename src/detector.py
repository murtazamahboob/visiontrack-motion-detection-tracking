"""Background modelling and motion detection.

The core works on plain NumPy arrays, so it can be tested with synthetic
frames and no camera. A live OpenCV camera is only an input adapter
(see camera.py); it is not required to run the detector, tracker or tests.
"""
from __future__ import annotations

import numpy as np


def to_grayscale(frame):
    """Convert an HxW or HxWx3 frame to a float grayscale array."""
    arr = np.asarray(frame, dtype=np.float64)
    if arr.ndim == 3:
        return arr.mean(axis=2)
    if arr.ndim != 2:
        raise ValueError("frame must be HxW or HxWx3")
    return arr


def connected_components(mask):
    """Label 4-connected components in a boolean mask.

    Returns a list of dicts with x, y, w, h, area and centroid. This is a
    small, dependency-free labelling pass: it is deliberately explicit
    rather than a one-line library call, so the behaviour is testable
    without OpenCV installed.
    """
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    components = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            pixels = []
            while stack:
                cy, cx = stack.pop()
                pixels.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            ys = [p[0] for p in pixels]
            xs = [p[1] for p in pixels]
            components.append(
                {
                    "x": int(min(xs)),
                    "y": int(min(ys)),
                    "w": int(max(xs) - min(xs) + 1),
                    "h": int(max(ys) - min(ys) + 1),
                    "area": int(len(pixels)),
                    "centroid": (float(sum(xs) / len(xs)), float(sum(ys) / len(ys))),
                }
            )
    return components


class BackgroundModel:
    """Running background: first frame, then a slow exponential update."""

    def __init__(self, alpha=0.05):
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.background = None

    def update(self, gray, motion_mask=None):
        if self.background is None:
            self.background = gray.copy()
            return
        if motion_mask is None:
            self.background = (1 - self.alpha) * self.background + self.alpha * gray
        else:
            # Do not let a moving object paint itself into the background.
            still = ~motion_mask
            self.background[still] = (
                (1 - self.alpha) * self.background[still] + self.alpha * gray[still]
            )


class MotionDetector:
    """Detect moving blobs by differencing against the background model."""

    def __init__(self, threshold=30.0, min_area=25, background_alpha=0.05):
        self.threshold = float(threshold)
        self.min_area = int(min_area)
        self.model = BackgroundModel(alpha=background_alpha)

    def detect(self, frame, update_background=True):
        gray = to_grayscale(frame)
        if self.model.background is None:
            self.model.update(gray)
            return []
        diff = np.abs(gray - self.model.background)
        mask = diff > self.threshold
        detections = [c for c in connected_components(mask) if c["area"] >= self.min_area]
        if update_background:
            self.model.update(gray, motion_mask=mask)
        return detections
