"""Gera build/pingpilot.ico a partir do logo da barra lateral (ui/index.html)."""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024  # desenha grande e reduz, para bordas suaves

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S // 5, fill=(14, 16, 20, 255))


def pt(x, y):  # coordenadas do SVG 32x32, com margem
    return (S * 0.1 + x / 32 * S * 0.8, S * 0.1 + y / 32 * S * 0.8)


d.polygon([pt(6, 26), pt(16, 4), pt(26, 26), pt(16, 20)], fill=(229, 52, 74, 255))
d.polygon([pt(16, 4), pt(26, 26), pt(16, 20)], fill=(255, 255, 255, 220))

img.save(os.path.join(HERE, "pingpilot.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "pingpilot.png"))
print("ok")
