import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether, Preformatted)

OUT = sys.argv[1]
F = "/usr/share/fonts/truetype/dejavu/"
from reportlab.lib.fonts import addMapping


INK = colors.HexColor("#1B1F2A")
MUTED = colors.HexColor("#5B6475")
ACCENT = colors.HexColor("#0E7C66")
SOFT = colors.HexColor("#E8F4F1")
WARN = colors.HexColor("#B4541A")
WARNBG = colors.HexColor("#FCF0E6")
CODEBG = colors.HexColor("#F2F3F6")
LINE = colors.HexColor("#D5D9E0")

ss = {
    "title": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=26, leading=31, textColor=INK, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="Helvetica", fontSize=12.5, leading=18, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=21, textColor=ACCENT, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=INK, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bl", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, leftIndent=14, bulletIndent=3, spaceAfter=3),
    "small": ParagraphStyle("sm", fontName="Helvetica", fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=3),
    "cell": ParagraphStyle("c", fontName="Helvetica", fontSize=9, leading=12.5, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=9, leading=12.5, textColor=INK),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.6, leading=12, textColor=INK),
    "box": ParagraphStyle("box", fontName="Helvetica", fontSize=9.6, leading=14, textColor=INK),
}

def P(t, s="body"): return Paragraph(t, ss[s])
def B(items): return [Paragraph(i, ss["bullet"], bulletText="•") for i in items]

def code(text):
    t = Table([[Preformatted(text, ss["code"])]], colWidths=[170*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), CODEBG), ("BOX", (0,0), (-1,-1), 0.5, LINE),
                           ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
                           ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t

def callout(title, text, warn=False):
    bg, fg = (WARNBG, WARN) if warn else (SOFT, ACCENT)
    t = Table([[Paragraph(f"<font name='Helvetica-Bold' color='{fg.hexval()}'>{title}</font><br/>{text}", ss["box"])]], colWidths=[170*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), bg), ("LINEBEFORE", (0,0), (0,-1), 3, fg),
                           ("LEFTPADDING", (0,0), (-1,-1), 10), ("RIGHTPADDING", (0,0), (-1,-1), 10),
                           ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    return t

def table(rows, widths, head=True):
    data = [[Paragraph(str(c), ss["cellb" if (head and i == 0) else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w*mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0,0), (-1,-1), 0.4, LINE), ("VALIGN", (0,0), (-1,-1), "TOP"),
          ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
          ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)]
    if head: st.append(("BACKGROUND", (0,0), (-1,0), SOFT))
    t.setStyle(TableStyle(st))
    return t

def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 8); c.setFillColor(MUTED)
    c.drawString(20*mm, 10*mm, "3D & Glass Effects for Websites  ·  Breaking Digital Tamil")
    c.drawRightString(190*mm, 10*mm, f"Page {d.page}")
    c.setStrokeColor(LINE); c.line(20*mm, 14*mm, 190*mm, 14*mm)
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=20*mm,
                      title="React Three Fiber & Liquid Glass JS: A Beginner's Guide", author="Breaking Digital Tamil",
                      subject="Adding 3D scenes and Apple-style glass effects to a website")
doc.addPageTemplates([PageTemplate(frames=[Frame(20*mm, 18*mm, 170*mm, 259*mm, id="f")], onPage=footer)])

s = []
M = lambda t: f"<font name='Courier'>{t}</font>"
s += [Spacer(1, 6*mm), P("React Three Fiber &amp; Liquid Glass JS", "title"),
      P("A beginner's guide to two free GitHub libraries that add eye-catching effects to a website: interactive 3D scenes, and Apple-style \"liquid glass\" buttons and panels.", "sub"),
      table([["", "React Three Fiber", "Liquid Glass JS"],
             ["Repo", "github.com/pmndrs/react-three-fiber", "github.com/dashersw/liquid-glass-js"],
             ["What it adds", "Interactive 3D scenes", "Apple-style glass buttons and panels"],
             ["Works with", "React websites only", "Any website (plain HTML/JavaScript)"],
             ["Version / updated", "v9.8.1 · updated Oct 2026", "No releases · last updated June 2025"],
             ["Licence", "MIT (free, commercial use OK)", "MIT (free, commercial use OK)"],
             ["Install", "npm package", "Copy files from the repo (not on npm)"]], [36, 67, 67]),
      Spacer(1, 5*mm)]

s += [P("Part 1: React Three Fiber", "h1"),
      P("What is it?", "h2"),
      P("<b>Three.js</b> is the most popular library for 3D graphics in the browser: spinning products, floating shapes, 3D scenes you can drag around. <b>React Three Fiber</b> (often called <b>R3F</b>) lets you build those Three.js scenes using <b>React components</b>, the same way you build the rest of a React website. Every Three.js feature works in it, with no slowdown, because it simply writes Three.js for you."),
      P("Who is it for?", "h2")] + B([
      "<b>Good fit:</b> websites built with React, Next.js or Vite + React, such as landing pages, portfolios and product showcases.",
      "<b>Not for:</b> plain HTML sites, WordPress or Webflow. It only works inside a React project.",
      "<b>Version match matters:</b> R3F v9 needs React 19, and R3F v8 needs React 18. Install the one that matches your project.",
      ])

s += [P("Step 1: Install", "h2"),
      P("Inside your React project folder, run:"),
      code("npm install three @react-three/fiber"),
      P("Using TypeScript? Also run " + M("npm install @types/three") + ".", "small"),
      P("Step 2: Your first 3D scene", "h2"),
      P("This makes two boxes that spin, change colour when you hover, and grow when you click:"),
      code("import { useRef, useState } from 'react'\nimport { Canvas, useFrame } from '@react-three/fiber'\n\nfunction Box(props) {\n  const ref = useRef()\n  const [hovered, hover] = useState(false)\n  const [clicked, click] = useState(false)\n  useFrame((state, delta) => (ref.current.rotation.x += delta))\n  return (\n    <mesh {...props} ref={ref} scale={clicked ? 1.5 : 1}\n      onClick={() => click(!clicked)}\n      onPointerOver={() => hover(true)}\n      onPointerOut={() => hover(false)}>\n      <boxGeometry args={[1, 1, 1]} />\n      <meshStandardMaterial color={hovered ? 'hotpink' : 'orange'} />\n    </mesh>\n  )\n}\n\nexport default function App() {\n  return (\n    <Canvas>\n      <ambientLight intensity={Math.PI / 2} />\n      <pointLight position={[10, 10, 10]} decay={0} intensity={Math.PI} />\n      <Box position={[-1.2, 0, 0]} />\n      <Box position={[1.2, 0, 0]} />\n    </Canvas>\n  )\n}"),
      P("The key ideas, in plain words:", "h2"),
      table([["Piece", "What it means"],
             [M("&lt;Canvas&gt;"), "The 3D area on your page. Everything 3D goes inside it."],
             [M("&lt;mesh&gt;"), "One 3D object. It needs a shape (geometry) and a surface (material)."],
             [M("&lt;boxGeometry&gt;"), "The shape: box, sphere, plane and more."],
             [M("&lt;meshStandardMaterial&gt;"), "How the surface looks: colour, shine and roughness."],
             [M("&lt;ambientLight&gt;") + ", " + M("&lt;pointLight&gt;"), "Lights. Without light, most materials look black."],
             [M("useFrame"), "Runs every frame (about 60 times a second). Use it for animation."]], [52, 118])]

s += [P("Step 3: Make it look pro with helpers", "h2")] + B([
      "<b>@react-three/drei</b>: ready-made helpers (camera controls, 3D text, environment lighting, loading 3D models). Install with " + M("npm install @react-three/drei") + ".",
      "<b>@react-three/postprocessing</b>: glow, bloom and depth-of-field effects.",
      "<b>@react-three/rapier</b>: physics, so objects fall, bounce and collide.",
      "Browse ready-made examples at <b>docs.pmnd.rs</b> and copy the closest one.",
      ])

s += [P("Part 2: Liquid Glass JS", "h1"),
      P("What is it?", "h2"),
      P("A small JavaScript library that recreates the <b>Apple \"Liquid Glass\" look</b>: frosted glass buttons and panels that bend (refract) and blur whatever is behind them, using WebGL. It's a community project <b>inspired by</b> Apple's design, not made by Apple."),
      P("What you get:", "h2")] + B([
      "<b>Three shapes:</b> rounded rectangle, circle and pill (capsule).",
      "<b>Glass buttons and containers</b>, including glass buttons inside a glass panel.",
      "<b>Adjustable effects:</b> blur, refraction strength, rim light, tint and ripple.",
      "<b>Works on any website</b>, no React needed. It uses one helper library, html2canvas.",
      ])

s += [P("Step 1: Get the files", "h2"),
      P("Liquid Glass JS is <b>not an npm package</b>. Download the repo (GitHub &gt; Code &gt; Download ZIP), then copy these files into your website folder:"),
      code("container.js   button.js   glass.css   styles.css"),
      P("Step 2: Add it to your page", "h2"),
      code("<link rel=\"stylesheet\" href=\"styles.css\" />\n<link rel=\"stylesheet\" href=\"glass.css\" />\n\n<script\n  src=\"https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js\">\n</script>\n<script src=\"container.js\"></script>\n<script src=\"button.js\"></script>\n\n<script>\n  const button = new Button({\n    text: 'Order Now',\n    size: 28,\n    type: 'pill',\n    tintOpacity: 0.3,\n    onClick: () => alert('Thanks!')\n  })\n  document.body.appendChild(button.element)\n</script>"),
      P("Step 3: A glass panel with buttons inside", "h2"),
      code("const panel = new Container({ type: 'pill', borderRadius: 24, tintOpacity: 0.3 })\npanel.addChild(new Button({ text: 'Menu', size: 24, type: 'pill' }))\npanel.addChild(new Button({ text: 'Cart', size: 24, type: 'circle' }))\ndocument.body.appendChild(panel.element)"),
      P("Main settings:", "h2"),
      table([["Option", "What it does", "Default"],
             [M("type"), M("'rounded'") + ", " + M("'circle'") + " or " + M("'pill'"), M("'rounded'")],
             [M("borderRadius"), "Corner roundness in pixels", "48"],
             [M("tintOpacity"), "How strong the glass tint is (0 to 1)", "0.2"],
             [M("text") + " / " + M("size"), "Button label and font size", "'Button' / 48"],
             [M("warp"), "Extra distortion in the centre of a button", "false"],
             [M("onClick"), "What happens when the button is clicked", "none"]], [38, 92, 40]),
      P("The glass effect looks best over a <b>colourful image or gradient</b> background. Over plain white there's nothing for it to bend.", "small")]

s += [P("Part 3: Build it with Claude Code (no coding needed)", "h1"),
      P("You don't have to write this code yourself. Open your project in Claude Code (or Cursor) and describe what you want, for example:"),
      code("Add a hero section using @react-three/fiber and @react-three/drei:\na slowly rotating 3D cake model on the right, soft studio lighting,\nand the user can drag to rotate it. Keep it fast on phones."),
      code("Using the files from github.com/dashersw/liquid-glass-js, add a\nglass pill-shaped navigation bar with 'Menu', 'Cakes' and 'Order'\nbuttons over the hero image."),
      P("Claude will install the packages, copy the files and write the code. You still need a project (Node.js installed), and it usually takes a few rounds of \"make it bigger / slower / softer\" to get it right.", "small")]

s += [P("Part 4: Things to know before you use them", "h1"),
      callout("Performance and phones",
              "Both libraries use <b>WebGL</b> (the graphics card). Heavy 3D scenes or many glass elements can make pages slow and drain phone batteries. "
              "Keep scenes simple, compress 3D models, and test on a real phone. Liquid Glass JS takes a snapshot of the page to create its effect, "
              "which can be slow on long pages.", warn=True),
      Spacer(1, 3*mm)] + B([
      "<b>React Three Fiber is actively maintained</b> by the Poimandres team, with a big ecosystem. Safe to rely on.",
      "<b>Liquid Glass JS is a small personal project</b>, not updated since June 2025 and not on npm. It's fine for experiments and landing pages, but check it still works in current browsers before using it on a client site.",
      "<b>Accessibility:</b> glass buttons over busy images can be hard to read. Keep text contrast high.",
      "<b>Licences:</b> both are MIT, so free to use, including for client and commercial work. Keep their licence notice in your code.",
      "<b>Not \"no code\":</b> these are code libraries. Claude Code can do the coding, but you need a website project to put them in.",
      ])

s += [P("Quick cheat sheet", "h1"),
      table([["I want to…", "Do this"],
             ["Add 3D to a React site", M("npm install three @react-three/fiber")],
             ["Get camera controls, 3D text and models", M("npm install @react-three/drei")],
             ["Make an object spin", "Change its rotation inside " + M("useFrame")],
             ["Add Apple-style glass buttons", "Copy container.js, button.js and the CSS files, then " + M("new Button({...})")],
             ["Put glass buttons in a glass bar", M("new Container({...})") + " + " + M("addChild(button)")],
             ["Make glass stronger", "Raise " + M("tintOpacity") + " or turn on " + M("warp")],
             ["Let AI build it", "Describe the effect to Claude Code and name the library"]], [62, 108])]

s += [Spacer(1, 5*mm), P("Sources", "h2")] + [P(x, "small") for x in [
      "React Three Fiber README, v9.8.1: github.com/pmndrs/react-three-fiber · Docs: docs.pmnd.rs",
      "Liquid Glass JS README and source: github.com/dashersw/liquid-glass-js · Live demo: dashersw.github.io/liquid-glass-js",
      "Checked by Breaking Digital Tamil, November 2026.",
      ]]
# glue each h1/h2 to the next flowable so headings never sit alone at a page bottom
out=[]; i=0
while i < len(s):
    f=s[i]
    if isinstance(f, Paragraph) and f.style.name in ('h1','h2') and i+1 < len(s):
        grp=[f]; j=i+1
        while j < len(s) and isinstance(s[j], Paragraph) and s[j].style.name in ('h1','h2','body'):
            grp.append(s[j]); j+=1
        if j < len(s): grp.append(s[j]); j+=1
        out.append(KeepTogether(grp)); i=j
    else:
        out.append(f); i+=1
doc.build(out)
print("saved", OUT)
