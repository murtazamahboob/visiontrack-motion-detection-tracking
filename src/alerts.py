"""Alert rules over tracks and zone state.

Rules are pure functions of the current state, so each one is unit-testable
without a camera: loitering, fast movement and crowding.
"""
from __future__ import annotations

import math


def evaluate_alerts(tracks, zone_monitor, frame_index, config):
    alerts = []
    loiter_frames = config.get("loiter_frames", 20)
    fast_speed = config.get("fast_speed", 25.0)
    crowd_limit = config.get("crowd_limit", 5)

    for track in tracks:
        history = track["history"]
        if len(history) >= 2:
            step = math.hypot(
                history[-1][0] - history[-2][0], history[-1][1] - history[-2][1]
            )
            if step >= fast_speed:
                alerts.append(
                    {"type": "fast_movement", "track_id": track["id"],
                     "frame": frame_index, "speed_px_per_frame": round(step, 2)}
                )
        for zone in zone_monitor.zones:
            dwell = zone_monitor.dwell(track["id"], zone.name, frame_index)
            if dwell is not None and dwell >= loiter_frames:
                alerts.append(
                    {"type": "loitering", "track_id": track["id"],
                     "zone": zone.name, "frame": frame_index, "dwell_frames": dwell}
                )
    if len(tracks) >= crowd_limit:
        alerts.append(
            {"type": "crowding", "track_count": len(tracks), "frame": frame_index}
        )
    return alerts
