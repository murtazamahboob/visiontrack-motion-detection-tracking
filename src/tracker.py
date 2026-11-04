"""Greedy centroid tracker with a disappearance grace period."""
from __future__ import annotations

import math


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class CentroidTracker:
    """Assign stable IDs to detections by nearest centroid.

    A track survives ``max_missed`` frames with no matching detection, so a
    one-frame occlusion or detector miss does not renumber the object.
    """

    def __init__(self, max_distance=40.0, max_missed=3):
        self.max_distance = float(max_distance)
        self.max_missed = int(max_missed)
        self._next_id = 1
        self.tracks = {}  # id -> track dict

    def _new_track(self, detection, frame_index):
        track_id = self._next_id
        self._next_id += 1
        track = {
            "id": track_id,
            "centroid": detection["centroid"],
            "box": {k: detection[k] for k in ("x", "y", "w", "h")},
            "first_seen": frame_index,
            "last_seen": frame_index,
            "missed": 0,
            "history": [detection["centroid"]],
        }
        self.tracks[track_id] = track
        return track

    def update(self, detections, frame_index):
        unmatched = list(detections)
        # Match each existing track to its nearest still-unmatched detection.
        for track in list(self.tracks.values()):
            if not unmatched:
                break
            best = min(unmatched, key=lambda d: _distance(track["centroid"], d["centroid"]))
            if _distance(track["centroid"], best["centroid"]) <= self.max_distance:
                track["centroid"] = best["centroid"]
                track["box"] = {k: best[k] for k in ("x", "y", "w", "h")}
                track["last_seen"] = frame_index
                track["missed"] = 0
                track["history"].append(best["centroid"])
                unmatched.remove(best)
        for detection in unmatched:
            self._new_track(detection, frame_index)
        # Age tracks that were not matched this frame, then drop the stale ones.
        for track_id, track in list(self.tracks.items()):
            if track["last_seen"] != frame_index:
                track["missed"] += 1
                if track["missed"] > self.max_missed:
                    del self.tracks[track_id]
        return list(self.tracks.values())

    def active(self):
        return list(self.tracks.values())
