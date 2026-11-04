# Architecture

```
frames -> MotionDetector -> CentroidTracker -> ZoneMonitor -> Alerts
                |                  |                |
         background model    stable IDs,        enter / exit
         + connected         grace period       + dwell time
           components
```

- **Detector** (`src/detector.py`): grayscale conversion, absolute difference
  against a running background, thresholding, then a dependency-free
  4-connected-component labelling pass. Small blobs below `min_area` are
  dropped as noise. The background updates only on still pixels, so a
  moving object does not paint itself into the background.
- **Tracker** (`src/tracker.py`): greedy nearest-centroid matching within
  `max_distance`. Unmatched detections become new tracks; unmatched tracks
  survive `max_missed` frames, so a one-frame miss does not renumber an object.
- **Zones** (`src/zones.py`): rectangular zones with per-track enter/exit
  events and dwell time, including exit when a track vanishes.
- **Alerts** (`src/alerts.py`): pure rules over current state — loitering
  (dwell >= threshold), fast movement (step >= threshold px/frame) and
  crowding (active tracks >= limit). No alert depends on a camera.
- **Pipeline** (`src/pipeline.py`): wires the four stages over any frame
  iterable and returns events, alerts and counts.

## Why this is not a simple project

- The labelling, matching, grace period and dwell logic are all explicit
  and tested, not delegated to a single library call.
- Failure modes are honest: unknown / tiny blobs are dropped, tracks are
  dropped after the grace period, and alerts are derived from measured
  dwell and speed, not invented scores.
- The whole system runs and tests offline with synthetic frames; the
  OpenCV camera is an optional input adapter, not a requirement.
