# Setup

```bash
pip install -r requirements.txt
python3 tests/test_vision.py
python3 demo/run_demo.py
```

## Use it in code

```python
from src.pipeline import VisionPipeline
from src.zones import Zone

pipeline = VisionPipeline({
    "zones": [Zone("door", 40, 0, 40, 80)],
    "alerts": {"loiter_frames": 20, "fast_speed": 25.0, "crowd_limit": 5},
})
result = pipeline.run(frames)  # any iterable of HxW or HxWx3 frames
print(result["events"], result["alerts"])
```

## Live camera (optional)

Install `opencv-python`, then feed `src.camera.live_frames()` into
`pipeline.run()`. Without it, use `src.camera.synthetic_frames()` — the
demo and all tests use the synthetic source.
