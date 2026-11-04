"""Wire detector -> tracker -> zones -> alerts over a frame sequence."""
from __future__ import annotations

from .alerts import evaluate_alerts
from .detector import MotionDetector
from .tracker import CentroidTracker
from .zones import ZoneMonitor


class VisionPipeline:
    def __init__(self, config=None):
        config = config or {}
        det = config.get("detector", {})
        trk = config.get("tracker", {})
        self.detector = MotionDetector(
            threshold=det.get("threshold", 30.0),
            min_area=det.get("min_area", 25),
            background_alpha=det.get("background_alpha", 0.05),
        )
        self.tracker = CentroidTracker(
            max_distance=trk.get("max_distance", 40.0),
            max_missed=trk.get("max_missed", 3),
        )
        self.zones = ZoneMonitor(config.get("zones", []))
        self.alert_config = config.get("alerts", {})

    def run(self, frames):
        events, alerts, frames_seen = [], [], 0
        for frame_index, frame in enumerate(frames):
            frames_seen += 1
            detections = self.detector.detect(frame)
            tracks = self.tracker.update(detections, frame_index)
            events.extend(self.zones.update(tracks, frame_index))
            alerts.extend(
                evaluate_alerts(tracks, self.zones, frame_index, self.alert_config)
            )
        return {
            "frames": frames_seen,
            "events": events,
            "alerts": alerts,
            "active_tracks": len(self.tracker.active()),
            "event_counts": {
                kind: sum(1 for e in events if e["type"] == kind)
                for kind in ("zone_enter", "zone_exit")
            },
            "alert_counts": {
                kind: sum(1 for a in alerts if a["type"] == kind)
                for kind in ("fast_movement", "loitering", "crowding")
            },
        }
