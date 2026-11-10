from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "panel.png"
    image = Image.new("RGB", (720, 960), "#f8f3e8")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 680, 920), outline="#222222", width=8)
    draw.text((80, 90), "P08 panel spike", fill="#222222")
    image.save(path)
    assert path.exists() and path.stat().st_size > 1000
print("template_image_ok")
