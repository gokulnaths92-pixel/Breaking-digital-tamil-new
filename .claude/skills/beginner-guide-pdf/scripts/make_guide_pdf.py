"""Build a Breaking Digital Tamil beginner's guide PDF from a JSON spec.

Usage: python3 make_guide_pdf.py spec.json output.pdf

Uses only the PDF's built-in fonts (Helvetica / Courier), so files stay small
(~15 KB) and can be uploaded to Google Drive as base64 in one call.
Those fonts only cover Latin-1: never put arrows (use "&gt;"), emoji or
non-Latin script in the spec. Text fields accept ReportLab mini-HTML:
<b>, <i>, <font name='Courier'>, &amp; &lt; &gt;.

Spec format:
{
  "title": "Tool Name",
  "subtitle": "One-sentence promise of the guide.",
  "footer": "Tool Name: A Beginner's Guide",
  "info": [["Version covered", "..."], ["Official repo", "..."], ...],   # 2-col key/value table, no header
  "sections": [
    {"h1": "1. What is it?"},
    {"h2": "Who is it for?"},
    {"p": "Body paragraph."},
    {"bullets": ["Point one", "Point two"]},
    {"code": "npm install thing"},                       # monospace box; keep lines under ~85 chars
    {"table": [["Header A", "Header B"], ["a", "b"]], "widths": [60, 110]},   # widths in mm, total 170
    {"callout": "Body text", "title": "Read this first", "warn": false},     # warn=true -> orange box
    {"small": "Footnote-sized muted text."},
    {"spacer": 3}                                         # mm
  ],
  "sources": ["github.com/owner/repo README, version x", "..."]
}
"""
import json
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)

INK = colors.HexColor("#1B1F2A")
MUTED = colors.HexColor("#5B6475")
ACCENT = colors.HexColor("#0E7C66")
SOFT = colors.HexColor("#E8F4F1")
WARN = colors.HexColor("#B4541A")
WARNBG = colors.HexColor("#FCF0E6")
CODEBG = colors.HexColor("#F2F3F6")
LINE = colors.HexColor("#D5D9E0")
BRAND = "Breaking Digital Tamil"
WIDTH = 170  # mm of usable page width

SS = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=26, leading=31, textColor=INK, spaceAfter=6),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=12.5, leading=18, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=21, textColor=ACCENT, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=INK, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, leftIndent=14, bulletIndent=3, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=12.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=9, leading=12.5, textColor=INK),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.6, leading=12, textColor=INK),
    "box": ParagraphStyle("box", fontName="Helvetica", fontSize=9.6, leading=14, textColor=INK),
}


def para(text, style="body"):
    return Paragraph(text, SS[style])


def code_box(text):
    t = Table([[Preformatted(text, SS["code"])]], colWidths=[WIDTH * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def callout(title, text, warn=False):
    bg, fg = (WARNBG, WARN) if warn else (SOFT, ACCENT)
    body = f"<font name='Helvetica-Bold' color='{fg.hexval()}'>{title}</font><br/>{text}" if title else text
    t = Table([[Paragraph(body, SS["box"])]], colWidths=[WIDTH * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, fg),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def grid(rows, widths=None, head=True):
    n = len(rows[0])
    widths = widths or [WIDTH / n] * n
    data = [[Paragraph(str(c), SS["cellb" if (head and i == 0) else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), SOFT))
    t.setStyle(TableStyle(st))
    return t


def block(item):
    if "h1" in item: return [para(item["h1"], "h1")]
    if "h2" in item: return [para(item["h2"], "h2")]
    if "p" in item: return [para(item["p"])]
    if "small" in item: return [para(item["small"], "small")]
    if "bullets" in item: return [Paragraph(b, SS["bullet"], bulletText="•") for b in item["bullets"]]
    if "code" in item: return [code_box(item["code"])]
    if "table" in item: return [grid(item["table"], item.get("widths"), item.get("header", True)), Spacer(1, 2 * mm)]
    if "callout" in item: return [callout(item.get("title", ""), item["callout"], item.get("warn", False)), Spacer(1, 3 * mm)]
    if "spacer" in item: return [Spacer(1, item["spacer"] * mm)]
    raise ValueError(f"Unknown block: {item}")


def keep_headings_with_next(flows):
    """Glue each heading (and any intro paragraphs) to the next block so headings never sit alone."""
    out, i = [], 0
    while i < len(flows):
        f = flows[i]
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2") and i + 1 < len(flows):
            grp, j = [f], i + 1
            while j < len(flows) and isinstance(flows[j], Paragraph) and flows[j].style.name in ("h1", "h2", "body"):
                grp.append(flows[j]); j += 1
            if j < len(flows):
                grp.append(flows[j]); j += 1
            out.append(KeepTogether(grp)); i = j
        else:
            out.append(f); i += 1
    return out


def build(spec, out_path):
    footer_text = f"{spec.get('footer', spec['title'] + ': A Beginner' + chr(39) + 's Guide')}  ·  {BRAND}"

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 8); c.setFillColor(MUTED)
        c.drawString(20 * mm, 10 * mm, footer_text)
        c.drawRightString(190 * mm, 10 * mm, f"Page {d.page}")
        c.setStrokeColor(LINE); c.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)
        c.restoreState()

    doc = BaseDocTemplate(out_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                          bottomMargin=20 * mm, title=spec.get("footer", spec["title"]), author=BRAND,
                          subject=spec.get("subtitle", ""))
    doc.addPageTemplates([PageTemplate(frames=[Frame(20 * mm, 18 * mm, WIDTH * mm, 259 * mm, id="f")], onPage=footer)])

    flows = [Spacer(1, 6 * mm), para(spec["title"], "title")]
    if spec.get("subtitle"):
        flows.append(para(spec["subtitle"], "sub"))
    if spec.get("info"):
        flows += [grid(spec["info"], spec.get("info_widths", [38, 132]), head=False), Spacer(1, 5 * mm)]
    for item in spec["sections"]:
        flows += block(item)
    if spec.get("sources"):
        flows += [Spacer(1, 5 * mm), para("Sources", "h2")] + [para(s, "small") for s in spec["sources"]]
    doc.build(keep_headings_with_next(flows))


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        spec = json.load(fh)
    bad = sorted({ch for ch in json.dumps(spec, ensure_ascii=False) if ord(ch) > 255 and ch not in "•·–—‘’“”…"})
    if bad:
        sys.exit(f"Characters the built-in fonts can't draw: {' '.join(bad)} -- replace them (e.g. arrows with '&gt;').")
    build(spec, sys.argv[2])
    print("saved", sys.argv[2])
