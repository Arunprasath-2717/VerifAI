"""Recolor the existing VerifAI mesh/globe hero for the light UI.

No new art is generated: this reuses the already-approved abstract wave asset.
Run: python3 frontend/scripts/recolor_hero_light.py
"""
from pathlib import Path
from PIL import Image, ImageEnhance
assets = Path(__file__).resolve().parents[1] / "src" / "assets"
src = assets / "hero_card_bg.png"
out = assets / "hero_card_light_green.webp"
im = Image.open(src).convert("RGB")
pixels = im.load()
for y in range(im.height):
    for x in range(im.width):
        r, g, b = pixels[x, y]
        warm = max(0, r - g)
        cream = max(0, r - b)
        pixels[x, y] = (
            max(0, min(255, round(r - 0.90 * warm))),
            max(0, min(255, round(g + 0.93 * warm))),
            max(0, min(255, round(b + 0.37 * warm + 0.05 * cream))),
        )
image = ImageEnhance.Contrast(im).enhance(1.06)
image.save(out, format="WEBP", quality=88, method=6)
print(f"Reused {src.name} → {out.name}: {image.width}x{image.height}, {out.stat().st_size:,} bytes")
