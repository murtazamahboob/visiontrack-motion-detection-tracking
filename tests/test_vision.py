"""Tests for VisionTrack: detector, tracker, zones, alerts and pipeline.

All tests use synthetic NumPy frames, so they run with no camera and
no OpenCV installed.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.camera import blank_frame, synthetic_frames
from src.detector import MotionDetector
from src.pipeline import VisionPipeline
from src.tracker import CentroidTracker
from src.zones import Zone, ZoneMonitor
from src.alerts import evaluate_alerts


def frame_with_square(x, y, size=12, width=120, height=80):
    frame = blank_frame(width, height)
    frame[y:y + size, x:x + size] = 255
    return frame


class TestDetector(unittest.TestCase):
    def test_finds_single_moving_square(self):
        det = MotionDetector()
        det.detect(blank_frame())
        detections = det.detect(frame_with_square(20, 30))
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["area"], 144)
        self.assertAlmostEqual(detections[0]["centroid"][0], 25.5, places=1)

    def test_ignores_static_frame(self):
        det = MotionDetector()
        det.detect(blank_frame())
        self.assertEqual(det.detect(blank_frame()), [])

    def test_ignores_small_noise_below_min_area(self):
        det = MotionDetector(min_area=25)
        det.detect(blank_frame())
        noisy = blank_frame()
        noisy[10:12, 10:12] = 255  # 4 pixels, below min_area
        self.assertEqual(det.detect(noisy), [])

    def test_finds_two_objects(self):
        det = MotionDetector()
        det.detect(blank_frame())
        frame = frame_with_square(10, 10)
        frame[50:62, 80:92] = 255
        self.assertEqual(len(det.detect(frame)), 2)


class TestTracker(unittest.TestCase):
    def test_keeps_same_id_across_frames(self):
        tracker = CentroidTracker()
        tracker.update([{"centroid": (20.0, 20.0), "x": 15, "y": 15, "w": 10, "h": 10}], 0)
        tracks = tracker.update([{"centroid": (23.0, 20.0), "x": 18, "y": 15, "w": 10, "h": 10}], 1)
        self.assertEqual([t["id"] for t in tracks], [1])

    def test_new_object_gets_new_id(self):
        tracker = CentroidTracker()
        tracker.update([{"centroid": (20.0, 20.0), "x": 15, "y": 15, "w": 10, "h": 10}], 0)
        tracks = tracker.update([
            {"centroid": (20.0, 20.0), "x": 15, "y": 15, "w": 10, "h": 10},
            {"centroid": (90.0, 60.0), "x": 85, "y": 55, "w": 10, "h": 10},
        ], 1)
        self.assertEqual(sorted(t["id"] for t in tracks), [1, 2])

    def test_drops_track_after_grace_period(self):
        tracker = CentroidTracker(max_missed=1)
        det = {"centroid": (20.0, 20.0), "x": 15, "y": 15, "w": 10, "h": 10}
        tracker.update([det], 0)
        tracker.update([], 1)  # missed once: still kept
        self.assertEqual(len(tracker.active()), 1)
        tracker.update([], 2)  # missed twice: dropped
        self.assertEqual(len(tracker.active()), 0)


class TestZonesAndAlerts(unittest.TestCase):
    def test_zone_enter_and_exit(self):
        monitor = ZoneMonitor([Zone("door", 40, 0, 40, 80)])
        track = {"id": 1, "centroid": (10.0, 30.0)}
        self.assertEqual(monitor.update([track], 0), [])
        track = {"id": 1, "centroid": (50.0, 30.0)}
        events = monitor.update([track], 1)
        self.assertEqual([e["type"] for e in events], ["zone_enter"])
        track = {"id": 1, "centroid": (90.0, 30.0)}
        events = monitor.update([track], 2)
        self.assertEqual(events[0]["type"], "zone_exit")
        self.assertEqual(events[0]["dwell_frames"], 1)

    def test_loitering_alert_after_dwell_threshold(self):
        monitor = ZoneMonitor([Zone("door", 0, 0, 120, 80)])
        track = {"id": 1, "centroid": (50.0, 30.0), "history": [(50.0, 30.0)]}
        monitor.update([track], 0)
        alerts = evaluate_alerts([track], monitor, 5, {"loiter_frames": 5})
        self.assertTrue(any(a["type"] == "loitering" for a in alerts))

    def test_fast_movement_alert(self):
        monitor = ZoneMonitor([])
        track = {"id": 1, "centroid": (60.0, 30.0),
                 "history": [(20.0, 30.0), (60.0, 30.0)]}
        alerts = evaluate_alerts([track], monitor, 1, {"fast_speed": 25.0})
        self.assertTrue(any(a["type"] == "fast_movement" for a in alerts))


class TestPipeline(unittest.TestCase):
    def test_pipeline_tracks_synthetic_motion_and_zone_entry(self):
        pipeline = VisionPipeline({
            "zones": [Zone("door", 40, 0, 40, 80)],
            "alerts": {"loiter_frames": 100, "fast_speed": 1000.0, "crowd_limit": 99},
        })
        frames = [blank_frame()] + list(synthetic_frames(count=20, start=(10, 30), step=(3, 0)))
        result = pipeline.run(frames)
        self.assertEqual(result["frames"], 21)
        self.assertEqual(result["event_counts"]["zone_enter"], 1)
        self.assertEqual(result["active_tracks"], 1)

    def test_pipeline_no_false_zone_alert_outside_zone(self):
        pipeline = VisionPipeline({"zones": [Zone("far", 100, 0, 20, 80)]})
        frames = [blank_frame()] + list(synthetic_frames(count=10, start=(10, 30), step=(2, 0)))
        result = pipeline.run(frames)
        self.assertEqual(result["event_counts"]["zone_enter"], 0)


if __name__ == "__main__":
    unittest.main()
