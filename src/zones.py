"""Rectangular zones: entry, exit and dwell tracking per object."""
from __future__ import annotations


class Zone:
    def __init__(self, name, x, y, w, h):
        self.name = name
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    def contains(self, point):
        px, py = point
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


class ZoneMonitor:
    """Emit enter/exit events and track how long each object stays inside."""

    def __init__(self, zones):
        self.zones = list(zones)
        self._inside = {}  # (track_id, zone_name) -> first frame index

    def update(self, tracks, frame_index):
        events = []
        present = set()
        for track in tracks:
            for zone in self.zones:
                key = (track["id"], zone.name)
                if zone.contains(track["centroid"]):
                    present.add(key)
                    if key not in self._inside:
                        self._inside[key] = frame_index
                        events.append(
                            {"type": "zone_enter", "track_id": track["id"],
                             "zone": zone.name, "frame": frame_index}
                        )
                elif key in self._inside:
                    dwell = frame_index - self._inside.pop(key)
                    events.append(
                        {"type": "zone_exit", "track_id": track["id"],
                         "zone": zone.name, "frame": frame_index, "dwell_frames": dwell}
                    )
        # A track that vanished entirely also exits any zone it was in.
        for key in list(self._inside):
            if key not in present:
                track_id, zone_name = key
                if not any(t["id"] == track_id for t in tracks):
                    dwell = frame_index - self._inside.pop(key)
                    events.append(
                        {"type": "zone_exit", "track_id": track_id,
                         "zone": zone_name, "frame": frame_index, "dwell_frames": dwell}
                    )
        return events

    def dwell(self, track_id, zone_name, frame_index):
        start = self._inside.get((track_id, zone_name))
        return None if start is None else frame_index - start
