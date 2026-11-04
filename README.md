# VisionTrack: OpenCV Motion Detection, Object Tracking and Zone Alerts

**OpenCV computer vision | motion detection | object tracking | centroid tracker | zone intrusion detection | loitering alerts | Python CV project**

VisionTrack is a real-time-style computer vision system: it detects moving
objects, gives each one a stable tracked ID, watches rectangular zones for
entry and exit, and raises alerts for loitering, fast movement and crowding.

This is not a single-frame demo. It is a four-stage pipeline — detector,
tracker, zones, alerts — with a background model that does not absorb moving
objects, a tracker grace period for missed frames, and dwell-time zone
logic, all tested offline with synthetic frames.

## How it works

```
frames -> MotionDetector -> CentroidTracker -> ZoneMonitor -> Alerts
```

1. **Detector** — differences each frame against a running background,
   thresholds it, and labels connected blobs, dropping noise below a
   minimum area.
2. **Tracker** — matches detections to tracks by nearest centroid, keeps a
   stable ID across frames, and only drops a track after a grace period
   of missed frames.
3. **Zones** — rectangular zones emit enter/exit events per track and
   measure dwell time, including exit when a track vanishes.
4. **Alerts** — loitering (dwell over threshold), fast movement (step over
   px/frame threshold) and crowding (active tracks over limit), all derived
   from measured state, not invented scores.

## Run it (no camera, no API key needed)

```bash
pip install -r requirements.txt
python3 tests/test_vision.py
python3 demo/run_demo.py
```

The demo runs a synthetic moving object across a "door" zone and prints
its zone entry and any alerts. To use a real camera, install
`opencv-python` and feed `src.camera.live_frames()` into the pipeline —
the core never requires OpenCV to run or test.

## Project structure

```text
src/        Detector, tracker, zones, alerts, pipeline, camera adapters
tests/      Detector, tracker, zone, alert and full-pipeline tests
demo/       Synthetic-frame demo printing events and alerts
samples/    Example pipeline config
docs/       Architecture and setup notes
```

## Why this is not a simple project

- **Explicit vision logic, not one library call** — connected-component
  labelling, greedy centroid matching and dwell tracking are implemented
  and tested in this repo.
- **Honest failure modes** — tiny blobs are dropped as noise, tracks expire
  after the grace period, and alerts come from measured dwell and speed.
- **Tested behaviour** — detection, noise rejection, ID stability, new
  IDs, grace-period expiry, zone entry/exit, loitering, fast movement
  and full-pipeline runs are all covered by tests.

## SEO and GitHub topics

Suggested GitHub topics: `opencv`, `computer-vision`, `motion-detection`,
`object-tracking`, `centroid-tracker`, `video-analytics`, `python`,
`ai-projects`, `surveillance`, `automation`

## License

MIT — see LICENSE.
