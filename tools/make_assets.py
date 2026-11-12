#!/usr/bin/env python3
"""Gera favicon.ico, assets/avatar-hero.webp e assets/og-cover.jpg a partir de assets/logo.png e assets/avatar.png.

Uso: python3 tools/make_assets.py   (só precisa rodar de novo se logo/avatar mudarem)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
BRAND = (10, 37, 64)  # #0a2540

# favicon.ico (multi-tamanho) na raiz
logo = Image.open(A / "logo.png").convert("RGBA")
logo.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

# avatar do hero: exibido em 96x96 -> 192x192 cobre telas 2x
avatar = Image.open(A / "avatar.png").convert("RGB")
avatar.resize((192, 192), Image.LANCZOS).save(A / "avatar-hero.webp", "WEBP", quality=82, method=6)

# imagem Open Graph 1200x630: avatar à esquerda + nome da marca
W, H = 1200, 630
og = Image.new("RGB", (W, H), BRAND)
d = ImageDraw.Draw(og)
size = 440
av = avatar.resize((size, size), Image.LANCZOS)
mask = Image.new("L", (size, size), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=48, fill=255)
og.paste(av, (80, (H - size) // 2), mask)

def font(name, px):
    for p in (f"/usr/share/fonts/truetype/sand-box/google/Poppins/{name}",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, px)
        except OSError:
            continue
    return ImageFont.load_default()

x = 580
d.text((x, 190), "J.A Instalações", font=font("Poppins-Bold.ttf", 72), fill="white")
d.text((x, 290), "Elétrica · Hidráulica · Telhados", font=font("Poppins-Medium.ttf", 38), fill=(227, 242, 253))
d.text((x, 350), "São Paulo e Grande São Paulo", font=font("Poppins-Medium.ttf", 38), fill=(227, 242, 253))
d.rectangle((x, 430, x + 120, 436), fill=(30, 136, 229))
d.text((x, 460), "jainstalacoes.com", font=font("Poppins-Medium.ttf", 32), fill=(160, 190, 220))
og.save(A / "og-cover.jpg", "JPEG", quality=84, optimize=True, progressive=True)
for f in (ROOT / "favicon.ico", A / "avatar-hero.webp", A / "og-cover.jpg"):
    print(f.relative_to(ROOT), f.stat().st_size, "bytes")
