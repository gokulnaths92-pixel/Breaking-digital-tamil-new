"""Render a Cake N Crumble end card (1080x1920) over a blurred background frame."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
BG, LOGO, OUT = sys.argv[1:4]
W, H = 1080, 1920
XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
bg = Image.open(BG).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(28))
bg = ImageEnhance.Brightness(bg).enhance(0.45).convert("RGBA")
logo = Image.open(LOGO).convert("RGBA")
logo = logo.resize((560, int(560 * logo.height / logo.width)), Image.LANCZOS)
bg.alpha_composite(logo, ((W - logo.width) // 2, 470))
d = ImageDraw.Draw(bg)
def center(t, f, y, fill):
    d.text(((W - f.getlength(t)) / 2, y), t, font=f, fill=fill)
f1 = ImageFont.truetype(XB, 92); f2 = ImageFont.truetype(SB, 46); f3 = ImageFont.truetype(SB, 40)
center("DM for", f2, 1110, "#F7C9D4")
center("Custom Cakes", f1, 1170, "white")
d.rounded_rectangle((W/2-60, 1300, W/2+60, 1306), radius=3, fill="#E8B84A")
center("@cake_n_crumble_03", f3, 1340, "white")
bg.convert("RGB").save(OUT)
print("saved", OUT)
