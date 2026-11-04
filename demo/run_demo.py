"""Demo: run VisionTrack over synthetic frames (no camera needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.camera import blank_frame, synthetic_frames
from src.pipeline import VisionPipeline
from src.zones import Zone

if __name__ == "__main__":
    pipeline = VisionPipeline({
        "zones": [Zone("door", 40, 0, 40, 80)],
        "alerts": {"loiter_frames": 8, "fast_speed": 25.0, "crowd_limit": 5},
    })
    frames = [blank_frame()] + list(
        synthetic_frames(count=30, start=(10, 30), step=(3, 0))
    )
    result = pipeline.run(frames)
    print(f"Frames: {result['frames']}, active tracks: {result['active_tracks']}")
    print(f"Events: {result['event_counts']}, alerts: {result['alert_counts']}")
    for event in result["events"]:
        print(event)
    for alert in result["alerts"]:
        print(alert)
