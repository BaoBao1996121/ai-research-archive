from pathlib import Path
import tempfile
import numpy as np
import imageio.v3 as iio

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "demo.mp4"
    frames = []
    for i in range(12):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[:, :, 0] = 30 + i * 10
        frame[:, :, 1] = 120
        frame[:, :, 2] = 200
        frames.append(frame)
    iio.imwrite(path, frames, fps=6)
    assert path.exists() and path.stat().st_size > 1000
print("mp4_encode_ok")
