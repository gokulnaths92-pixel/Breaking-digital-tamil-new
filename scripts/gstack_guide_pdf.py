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
pdfmetrics.registerFont(TTFont("Sans", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", F + "DejaVuSansMono.ttf"))
from reportlab.lib.fonts import addMapping
addMapping("Sans", 0, 0, "Sans"); addMapping("Sans", 1, 0, "Sans-Bold")

INK = colors.HexColor("#1B1F2A")
MUTED = colors.HexColor("#5B6475")
ACCENT = colors.HexColor("#0E7C66")
SOFT = colors.HexColor("#E8F4F1")
WARN = colors.HexColor("#B4541A")
WARNBG = colors.HexColor("#FCF0E6")
CODEBG = colors.HexColor("#F2F3F6")
LINE = colors.HexColor("#D5D9E0")

ss = {
    "title": ParagraphStyle("t", fontName="Sans-Bold", fontSize=26, leading=31, textColor=INK, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="Sans", fontSize=12.5, leading=18, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=16, leading=21, textColor=ACCENT, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=12, leading=16, textColor=INK, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="Sans", fontSize=10, leading=15, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bl", fontName="Sans", fontSize=10, leading=15, textColor=INK, leftIndent=14, bulletIndent=3, spaceAfter=3),
    "small": ParagraphStyle("sm", fontName="Sans", fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=3),
    "cell": ParagraphStyle("c", fontName="Sans", fontSize=9, leading=12.5, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="Sans-Bold", fontSize=9, leading=12.5, textColor=INK),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=8.6, leading=12, textColor=INK),
    "box": ParagraphStyle("box", fontName="Sans", fontSize=9.6, leading=14, textColor=INK),
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
    t = Table([[Paragraph(f"<font name='Sans-Bold' color='{fg.hexval()}'>{title}</font><br/>{text}", ss["box"])]], colWidths=[170*mm])
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
    c.setFont("Sans", 8); c.setFillColor(MUTED)
    c.drawString(20*mm, 10*mm, "gstack: A Beginner's Guide  ·  Breaking Digital Tamil")
    c.drawRightString(190*mm, 10*mm, f"Page {d.page}")
    c.setStrokeColor(LINE); c.line(20*mm, 14*mm, 190*mm, 14*mm)
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=20*mm,
                      title="gstack: A Beginner's Guide", author="Breaking Digital Tamil",
                      subject="How to install and use gstack with Claude Code")
doc.addPageTemplates([PageTemplate(frames=[Frame(20*mm, 18*mm, 170*mm, 259*mm, id="f")], onPage=footer)])

s = []
s += [Spacer(1, 6*mm), P("gstack", "title"),
      P("A beginner's guide to Garry Tan's free Claude Code setup: slash commands that act like a product, design, engineering, QA and release team for one builder.", "sub"),
      table([["Version covered", "gstack 1.100 (November 2026)"],
             ["Official repo", "github.com/garrytan/gstack (copies under other names are not official)"],
             ["Made by", "Garry Tan, President &amp; CEO of Y Combinator, shared as open source"],
             ["Cost", "Free (MIT licence). You still need Claude Code, which needs a Claude plan or API usage."],
             ["Works on", "macOS and Linux fully; Windows 11 via Git Bash or WSL (basic support)"]], [38, 132], head=False),
      Spacer(1, 5*mm)]

s += [P("1. What is gstack?", "h1"),
      P("Claude Code is an AI that writes code in your terminal. On its own it waits for instructions. <b>gstack adds ready-made \"roles\"</b> to it as slash commands, so instead of a blank prompt you get a structured team: someone who questions your idea, someone who plans the architecture, a reviewer, a tester and a release engineer."),
      P("gstack follows the steps of a real software sprint:", "h2"),
      callout("Think → Plan → Build → Review → Test → Ship → Reflect",
              "Each command writes notes that the next one reads. <font name='Mono'>/office-hours</font> writes a design doc, "
              "<font name='Mono'>/plan-eng-review</font> turns it into a plan and test list, <font name='Mono'>/qa</font> tests against it, "
              "and <font name='Mono'>/ship</font> checks everything before opening a pull request."),
      Spacer(1, 2*mm)]

s += [P("2. Who should use it?", "h1")] + B([
      "<b>Good fit:</b> people who already use Claude Code (or Codex) to build apps, such as founders, solo developers, vibe coders and tech leads.",
      "<b>Not for:</b> people who only use the ChatGPT or Claude chat apps. gstack needs the terminal, Git and a code project.",
      "<b>Start small.</b> gstack has 60+ commands. Its own README says to begin with just three: <font name='Mono'>/office-hours</font>, <font name='Mono'>/review</font> and <font name='Mono'>/qa</font>.",
      ])

s += [P("3. Before you start", "h1")] + B([
      "<b>Claude Code</b> installed and signed in (code.claude.com).",
      "<b>Git</b> (git-scm.com).",
      "<b>Bun</b> version 1.4.2 or newer (bun.sh). Setup refuses Bun older than 1.3.3 for safety.",
      "<b>Node.js</b> too if you're on Windows.",
      "<b>A project folder</b> with your code, ideally a Git repository.",
      ])

s += [P("4. Install gstack (about 30 seconds)", "h1"),
      P("Open Claude Code and paste this message. Claude will run the install for you:"),
      code("Install gstack: run git clone --single-branch --depth 1\nhttps://github.com/garrytan/gstack.git ~/.claude/skills/gstack\n&& cd ~/.claude/skills/gstack && ./setup"),
      P("Or run it yourself in a terminal:"),
      code("git clone --single-branch --depth 1 \\\n  https://github.com/garrytan/gstack.git ~/.claude/skills/gstack\ncd ~/.claude/skills/gstack\n./setup"),
      P("On Windows, from PowerShell, run <font name='Mono'>.\\setup.ps1</font> inside the gstack folder instead. It checks for Git, Bun and Node and tells you what's missing.", "small"),
      callout("What setup changes on your computer",
              "It installs the skills into <font name='Mono'>~/.claude/skills</font>, builds a small browser tool, and <b>adds a hook to your Claude Code settings</b> automatically. "
              "The official install message also asks Claude to add a gstack section to your <font name='Mono'>CLAUDE.md</font> file, telling it to use gstack's browser. "
              "All of this is documented and can be removed, but it does more than just copy files.", warn=True),
      Spacer(1, 2*mm)]

s += [P("5. Your first session: the three starter commands", "h1"),
      table([["Command", "Role", "What it does for you"],
             ["<font name='Mono'>/office-hours</font>", "YC-style mentor", "Asks six hard questions about your idea, pushes back on your framing, suggests options and writes a design doc. Start here for any new idea."],
             ["<font name='Mono'>/review</font>", "Staff engineer", "Reads your changes and looks for bugs that pass tests but break in production. Fixes the obvious ones and asks you about the rest."],
             ["<font name='Mono'>/qa</font>", "QA lead", "Opens a real browser on your app (for example <font name='Mono'>/qa http://localhost:3000</font>), clicks through it, finds bugs, fixes them and re-checks."]], [32, 32, 106]),
      Spacer(1, 2*mm),
      P("Try it like this:", "h2"),
      code("You:    /office-hours\n        I want to build an order form for my cake shop.\nClaude: [asks about the real problem, challenges assumptions,\n         suggests 3 approaches, writes a design doc]\n\nYou:    (build the feature with Claude as usual)\n\nYou:    /review\nYou:    /qa http://localhost:3000")]

s += [P("6. The full team: other useful commands", "h1"),
      table([["Stage", "Command", "What it does"],
             ["Plan", "<font name='Mono'>/plan-ceo-review</font>", "Rethinks scope: should this be bigger, smaller or different?"],
             ["Plan", "<font name='Mono'>/plan-eng-review</font>", "Locks architecture, data flow, edge cases and the test plan"],
             ["Plan", "<font name='Mono'>/plan-design-review</font>", "Scores the design 0–10 and edits the plan to improve it"],
             ["Plan", "<font name='Mono'>/autoplan</font>", "Runs the CEO, design, developer-experience and engineering reviews in one go"],
             ["Design", "<font name='Mono'>/design-shotgun</font>", "Makes 4–6 mockup options to compare and pick from"],
             ["Build", "<font name='Mono'>/verify</font>", "Runs your typecheck, lint, build and tests, and fixes failures until green"],
             ["Security", "<font name='Mono'>/cso</font>", "A security audit of your app (some modes need extra tools such as Docker)"],
             ["Ship", "<font name='Mono'>/ship</font>", "Syncs, runs tests, checks coverage and docs, then pushes and opens a pull request"],
             ["Ship", "<font name='Mono'>/land-and-deploy</font>", "Merges the PR, waits for CI and the deploy, then checks production"],
             ["After", "<font name='Mono'>/canary</font>", "Watches the live site for errors after a deploy"],
             ["Reflect", "<font name='Mono'>/retro</font>", "A weekly summary of what you shipped and what to improve"]], [20, 42, 108]),
      Spacer(1, 2*mm),
      P("Not sure which review to run? For apps people use, use <font name='Mono'>/plan-design-review</font> before coding and <font name='Mono'>/design-review</font> after. For code quality, use <font name='Mono'>/plan-eng-review</font> before and <font name='Mono'>/review</font> after. To cover everything at once, use <font name='Mono'>/autoplan</font>.", "small")]

s += [P("7. Privacy settings to check", "h1")] + B([
      "<b>Usage telemetry</b> is <b>off</b> by default. gstack asks once whether you want it on.",
      "<b>Update check</b> is <b>on</b>: it contacts GitHub to see if there's a new version. Turn it off with <font name='Mono'>gstack-config set update_check false</font>.",
      "<b>\"Outside reviews\"</b> are <b>on</b>: gstack can send your code to Codex or Claude Code (using your own login) for a second opinion. Turn them off with <font name='Mono'>gstack-config set codex_reviews disabled</font>.",
      "<b>Logged-in browsing:</b> on a Mac with the Aside browser, the browser skills can use your <b>real logged-in sessions</b>, and one skill can import cookies from Chrome. That's powerful for testing, but it means the AI can act as you on websites. Only use it on your own apps.",
      "<b>Auto-updates in team mode:</b> team mode checks for updates at most once an hour and installs new releases without asking.",
      ])

s += [P("8. What we found when we tested it", "h1"),
      P("We installed gstack in a clean test environment and tried it:"),
      table([["Test", "Result"],
             ["Install", "<b>Worked.</b> Setup finished in 18 seconds and installed 60+ skills."],
             ["Browser tool (engine behind /qa)", "<b>Worked.</b> It opened a test page, listed the fields and buttons, filled the form, clicked, read the page and took a screenshot."],
             ["Catching a page crash", "<b>Missed it.</b> Our test page had a JavaScript error on button click. gstack's error log showed only a harmless missing-icon message, not the crash. An AI using /qa could still notice the missing result, but don't rely on the error log alone."],
             ["Its own test suite", "Very large (2,000+ test files) and didn't finish in 10 minutes. The failures we saw needed tools our test machine didn't have (extra browser build, Docker, iOS tools)."],
             ["AI commands on a real project", "Not tested. /office-hours, /review and /ship depend on Claude doing real work on your code, so try them on a small project first."]], [48, 122])]

s += [P("9. Tips and safe habits", "h1")] + B([
      "<b>Start with three commands</b>, not sixty. Add more once those feel natural.",
      "<b>Work on a branch</b>, not straight on main, so you can throw away anything you don't like.",
      "<b>Read what /review and /ship change</b> before you merge. gstack is a helper, not a guarantee.",
      "<b>Use /qa on local or staging sites</b>, never on someone else's live website.",
      "<b>Expect AI usage costs.</b> Big commands like /autoplan and /ship use a lot of Claude tokens.",
      "<b>Update</b> with <font name='Mono'>/gstack-upgrade</font>, and <b>remove it</b> any time with <font name='Mono'>~/.claude/skills/gstack/bin/gstack-uninstall</font>.",
      ])

s += [P("10. Quick cheat sheet", "h1"),
      table([["I want to…", "Do this"],
             ["Install", "<font name='Mono'>git clone … ~/.claude/skills/gstack</font> then <font name='Mono'>./setup</font>"],
             ["Get feedback on an idea", "<font name='Mono'>/office-hours</font>"],
             ["Plan before coding", "<font name='Mono'>/autoplan</font> (or <font name='Mono'>/plan-eng-review</font>)"],
             ["Find bugs in my changes", "<font name='Mono'>/review</font>"],
             ["Test my app in a browser", "<font name='Mono'>/qa http://localhost:3000</font>"],
             ["Check security", "<font name='Mono'>/cso</font>"],
             ["Open a pull request safely", "<font name='Mono'>/ship</font>"],
             ["Stop sending code for outside reviews", "<font name='Mono'>gstack-config set codex_reviews disabled</font>"],
             ["Update or remove gstack", "<font name='Mono'>/gstack-upgrade</font> · <font name='Mono'>bin/gstack-uninstall</font>"]], [62, 108])]

s += [Spacer(1, 5*mm), P("Sources", "h2")] + [P(x, "small") for x in [
      "gstack README and docs, version 1.100: github.com/garrytan/gstack",
      "gstack uninstall guide: docs/uninstall.md · Support tiers: docs/support-tiers.md",
      "Hands-on test by Breaking Digital Tamil, November 2026 (install, browser tool and test suite).",
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
