"""Render the Children's Day header + caption overlay (720x1280 transparent PNG)."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
W, H = 720, 1280
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
XBOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
ef = ImageFont.truetype(EMOJI, 109)

def emoji(ch, size):
    im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=ef, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)

def is_emoji(c):
    return ord(c) > 0x2500

def runs(text):
    out, buf = [], ""
    for c in text:
        if c == "️":
            continue
        if is_emoji(c):
            if buf: out.append(("t", buf)); buf = ""
            out.append(("e", c))
        else:
            buf += c
    if buf: out.append(("t", buf))
    return out

def line_width(text, font, esize):
    w = 0
    for k, s in runs(text):
        w += font.getlength(s) if k == "t" else emoji(s, esize).width + 6
    return w

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)

def draw_line(text, font, y, fill, stroke, sw, esize, cx=W // 2):
    x = cx - line_width(text, font, esize) / 2
    for k, s in runs(text):
        if k == "t":
            d.text((x, y), s, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke)
            x += font.getlength(s)
        else:
            e = emoji(s, esize)
            asc = font.getbbox("A")
            layer.alpha_composite(e, (int(x + 3), int(y + asc[1] + (asc[3] - asc[1] - esize) / 2)))
            x += e.width + 6

# --- soft shadow helper: draw on separate layer, blur, composite under
def shadowed(fn):
    global layer, d
    base = layer
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer, d = tmp, ImageDraw.Draw(tmp)
    fn()
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(tmp.getchannel("A").point(lambda a: int(a * 0.55)))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    out = base.copy()
    out.alpha_composite(sh, (0, 6))
    out.alpha_composite(tmp)
    layer, d = out, ImageDraw.Draw(out)

# 1) date pill
def pill():
    f = ImageFont.truetype(XBOLD, 26)
    t = "🎈  14 NOVEMBER  🎈"
    w = line_width(t, f, 30) + 44
    x0 = (W - w) / 2
    d.rounded_rectangle((x0, 78, x0 + w, 126), radius=24, fill="#FFD43B")
    draw_line(t, f, 86, "#3B1F0E", None, 0, 30)
shadowed(pill)

# 2) HAPPY
def happy():
    f = ImageFont.truetype(BLACK, 50)
    draw_line("HAPPY", f, 140, "white", "#7B2FF7", 5, 0)
shadowed(happy)

# 3) CHILDREN'S DAY in rainbow letters
def title():
    f = ImageFont.truetype(BLACK, 74)
    text = "CHILDREN'S DAY"
    colors = ["#FF3B5C", "#FF8A00", "#FFD000", "#2ECC71", "#00B8F0", "#7B2FF7"]
    x = (W - f.getlength(text)) / 2
    i = 0
    for c in text:
        col = colors[i % len(colors)] if c != " " else "white"
        if c not in " ": i += 1
        d.text((x, 200), c, font=f, fill=col, stroke_width=7, stroke_fill="white")
        x += f.getlength(c)
shadowed(title)

# 4) caption
def caption():
    f = ImageFont.truetype(XBOLD, 38)
    draw_line("Tag your parents and ask them", f, 316, "white", "black", 4, 0)
    draw_line("to buy for you 😋❤️", f, 364, "white", "black", 4, 40)
shadowed(caption)

layer.save(OUT)
print("saved", OUT)
