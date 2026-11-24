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
    c.drawString(20*mm, 10*mm, "OmniRoute: A Beginner's Guide  ·  Breaking Digital Tamil")
    c.drawRightString(190*mm, 10*mm, f"Page {d.page}")
    c.setStrokeColor(LINE); c.line(20*mm, 14*mm, 190*mm, 14*mm)
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=20*mm,
                      title="OmniRoute: A Beginner's Guide", author="Breaking Digital Tamil",
                      subject="How to use OmniRoute and switch between AI models")
doc.addPageTemplates([PageTemplate(frames=[Frame(20*mm, 18*mm, 170*mm, 259*mm, id="f")], onPage=footer)])

s = []
s += [Spacer(1, 6*mm), P("OmniRoute", "title"),
      P("A beginner's guide to using many AI models through one free gateway, and keeping your work going by switching models automatically when one runs out.", "sub"),
      table([["Version covered", "OmniRoute 3.8.55 (November 2026)"],
             ["Official repo", "github.com/diegosouzapw/OmniRoute (also listed as cheaper-inference/OmniRoute)"],
             ["Cost", "Free and open source (MIT licence). You pay only for paid providers you choose to add."],
             ["Runs on", "Your own computer (Windows, Mac, Linux), a server, or Docker"]], [38, 132], head=False),
      Spacer(1, 5*mm)]

s += [P("1. What is OmniRoute?", "h1"),
      P("Think of OmniRoute as a <b>switchboard for AI models</b>. Normally every AI service (Gemini, Groq, OpenRouter, Claude, ChatGPT and so on) has its own website, its own key and its own limits. OmniRoute sits on your computer and gives you <b>one single address</b> that all your AI tools can talk to. Behind that address it decides which model answers each request."),
      P("Why that matters for a beginner:", "h2")] + B([
      "<b>One setup, many models.</b> Connect a provider once, then any tool (Claude Code, Codex, Cursor, Cline, VS Code Copilot) can use it.",
      "<b>Automatic switching.</b> If one model hits its limit or goes down, OmniRoute moves to the next one on your list without you doing anything.",
      "<b>Free providers first.</b> It knows which providers have free tiers, so you can build a setup that costs nothing.",
      "<b>Runs locally.</b> The gateway runs on your machine. Your prompts go only to the provider that answers them, not through an extra company server.",
      ])

s += [P("2. The honest truth about \"unlimited\"", "h1"),
      callout("Read this first",
              "No AI provider gives truly unlimited free use. Every free tier has a limit per minute, per day or per month. "
              "What OmniRoute does is <b>stack many free tiers together</b> and switch between them automatically. When one runs out, "
              "the next one takes over, so in daily use it can <b>feel</b> unlimited. OmniRoute's own docs estimate about "
              "<b>1.62 billion tokens per month</b> across all the free tiers it knows about, but that's only if you sign up for "
              "each provider yourself, and the number changes as providers change their offers."),
      Spacer(1, 3*mm),
      KeepTogether([P("How the switching works, in plain words:", "h2"),
      table([["Step", "What happens"],
             ["1", "You send a question to OmniRoute with the model set to <b>auto</b> (or to your own list, called a <b>combo</b>)."],
             ["2", "OmniRoute picks the best available model, for example a free Groq model."],
             ["3", "If that model says \"limit reached\" or fails, OmniRoute marks it as cooling down and tries the next model in line, for example Gemini Flash."],
             ["4", "When that one runs out, it moves on again: OpenRouter free models, NVIDIA NIM, Cloudflare AI and so on."],
             ["5", "When the first provider's limit resets (next minute, next day), it becomes available again."]], [14, 156])]),
      Spacer(1, 2*mm),
      P("OmniRoute has three built-in safety layers for this: it pauses a whole provider if it keeps failing, pauses just one key that hit a rate limit, and locks just one model that is unavailable, so the rest keep working.", "small")]

s += [P("3. Before you start", "h1")] + B([
      "<b>Node.js</b> version 22 or 24 (download from nodejs.org). Check with <font name='Mono'>node -v</font>.",
      "A <b>terminal</b> (Command Prompt / PowerShell on Windows, Terminal on Mac).",
      "Free accounts with a few AI providers (step 5 below). You get these yourself, since OmniRoute doesn't give you keys.",
      ])

s += [P("4. Install and start OmniRoute", "h1"),
      P("Open your terminal and run:"),
      code("npm install -g omniroute\nomniroute"),
      P("Then open the dashboard in your browser:"),
      code("Dashboard:  http://localhost:20128\nAPI:        http://localhost:20128/v1"),
      P("If npm shows <i>ERESOLVE</i> or peer-dependency warnings, they are harmless. If you use npm 11 or newer and it blocks install scripts, follow the exact command npm prints (OmniRoute's README lists it).", "small")]

s += [P("5. Connect free providers", "h1"),
      P("In the dashboard go to <b>Providers</b>, pick a provider, and paste its API key. Good free starting points:"),
      table([["Provider", "What you get free", "How to get the key"],
             ["Groq", "Fast Llama, GPT-OSS and Qwen models (about 15M tokens/month, with rate limits)", "Sign up at console.groq.com and create an API key"],
             ["Google Gemini", "Gemini Flash models (limits vary per model and project)", "Create a key in Google AI Studio"],
             ["OpenRouter", "Models ending in <font name='Mono'>:free</font> (shared request limits)", "Sign up at openrouter.ai and create a key"],
             ["NVIDIA NIM", "Many open models (about 40 requests per minute)", "Sign up at build.nvidia.com"],
             ["Cloudflare AI", "50+ models (about 10,000 \"neurons\" per day)", "Cloudflare account, then an API token"],
             ["Cerebras", "One-time $5 credit, expires after 30 days (card needed)", "Sign up at cerebras.ai"]], [30, 72, 68]),
      Spacer(1, 2*mm),
      P("Free limits change often. OmniRoute's dashboard page <font name='Mono'>/dashboard/free-tiers</font> shows what you have used and what is left.", "small")]

s += [P("6. Test that it works", "h1"),
      P("In the dashboard, open <b>Endpoints</b> and copy your OmniRoute API key. Then run:"),
      code('curl http://localhost:20128/v1/chat/completions \\\n  -H "Authorization: Bearer YOUR_OMNIROUTE_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model":"auto","messages":[{"role":"user","content":"Hello!"}]}\''),
      P("If you get a reply, everything works. To see every model you can now use:"),
      code('curl http://localhost:20128/v1/models -H "Authorization: Bearer YOUR_OMNIROUTE_KEY"')]

s += [P("7. Switching models: the easy way (auto)", "h1"),
      P("You don't have to build anything. Just set the model name to one of these, and OmniRoute builds a smart list from the providers you connected:"),
      table([["Model name", "Best for"],
             ["<font name='Mono'>auto</font>", "Balanced default; sticks with the last provider that worked"],
             ["<font name='Mono'>auto/coding</font>", "Best quality for writing code"],
             ["<font name='Mono'>auto/fast</font>", "Fastest replies"],
             ["<font name='Mono'>auto/cheap</font>", "Lowest cost first"],
             ["<font name='Mono'>auto/offline</font>", "The provider with the most quota left first, so you're less likely to hit limits"],
             ["<font name='Mono'>auto/subscription</font>", "Only uses subscriptions you already pay for, never a paid API by surprise"],
             ["<font name='Mono'>auto/thrifty</font>", "Your plan first, then the cheapest paid options, then back to the plan when it resets"]], [45, 125])]

s += [P("8. Switching models: build your own list (combo)", "h1"),
      P("A <b>combo</b> is your own ordered list of models. Create one in the dashboard under <b>Combos</b>, or from the terminal. This example rotates between three free models:"),
      code('omniroute combo create free-stack \\\n  --models "groq/llama-3.3-70b-versatile,gemini/gemini-2.5-flash,cerebras/gpt-oss-120b" \\\n  --strategy round-robin'),
      P("Then use <font name='Mono'>free-stack</font> as the model name in your tool. Useful strategies:")] + B([
      "<b>priority</b>: always try model 1 first and only fall back when it fails. Best when you have a favourite model.",
      "<b>round-robin</b>: take turns between models, which spreads usage so no single free tier runs out fast.",
      "<b>headroom / quota-weighted</b>: prefer whichever model has the most free quota left.",
      "<b>cost-optimized</b>: cheapest model first.",
      ]) + [P("Handy commands:", "h2"),
      code("omniroute combos list            # see your combos\nomniroute combos switch NAME     # make a combo the default\nomniroute models                 # list available models\nomniroute quota                  # see how much quota each provider has left\nomniroute health                 # check which providers are healthy")]

s += [P("9. Use it with your AI tools", "h1"),
      P("<b>Cursor, Cline, Continue, VS Code and most other apps</b>: look for \"OpenAI-compatible\" or \"custom provider\" settings and enter:"),
      code("Base URL:  http://localhost:20128/v1\nAPI key:   (your key from Dashboard → Endpoints)\nModel:     auto   (or your combo name, e.g. free-stack)"),
      P("<b>Claude Code</b>: the simplest way is to let OmniRoute launch it for you:"),
      code("omniroute launch\n\n# or create a profile for a specific model, then launch it\nomniroute setup-claude\nomniroute launch --profile glm52"),
      P("Claude Code can also be pointed at OmniRoute manually with the environment variables <font name='Mono'>ANTHROPIC_BASE_URL=http://localhost:20128</font> (no /v1 at the end) and <font name='Mono'>ANTHROPIC_AUTH_TOKEN=your-omniroute-key</font>.", "small")]

s += [P("10. Stay safe: rules every beginner should follow", "h1"),
      callout("Don't break providers' rules to get \"more free\"",
              "Use <b>one account per provider</b> unless that provider's terms say multiple accounts are allowed. Creating extra accounts "
              "to dodge free limits can get all of them banned. OmniRoute's own docs say to add accounts only \"without violating provider terms\". "
              "Some providers are flagged <font name='Mono'>tos: avoid</font> in OmniRoute's catalog (for example Kiro), and <b>auto</b> skips them by default. "
              "Connecting an account doesn't change that, so think twice before overriding it.", warn=True),
      Spacer(1, 3*mm)] + B([
      "<b>Check privacy before sending private work.</b> Some free providers log or use your prompts. For example, OmniRoute's guide notes that on Logfare <i>every request is logged</i>. Don't send passwords, client data or private code to providers whose privacy terms you haven't read.",
      "<b>Free models are not all equal.</b> When OmniRoute switches to a backup model, answers can be weaker or a different style. Check important output.",
      "<b>Limits change.</b> Free tiers end or shrink without warning. The ~1.62B tokens/month figure is an estimate that OmniRoute re-checks every two weeks, and it can go down.",
      "<b>Keep your keys secret.</b> Never share your OmniRoute key or provider keys in screenshots, videos or GitHub.",
      "<b>Watch paid fallbacks.</b> If you add paid API keys, use <font name='Mono'>auto/subscription</font> or a free-only combo so you're never charged by surprise.",
      ])

s += [P("11. Quick cheat sheet", "h1"),
      table([["I want to…", "Do this"],
             ["Install", "<font name='Mono'>npm install -g omniroute</font> then <font name='Mono'>omniroute</font>"],
             ["Open the dashboard", "http://localhost:20128"],
             ["Add a free provider", "Dashboard → Providers → paste API key"],
             ["Get my OmniRoute key", "Dashboard → Endpoints"],
             ["Let OmniRoute choose the model", "Use model name <font name='Mono'>auto</font>"],
             ["Never run out (as far as free tiers allow)", "Connect 4–6 free providers and use <font name='Mono'>auto/offline</font> or a round-robin combo"],
             ["See how much free quota is left", "<font name='Mono'>omniroute quota</font> or /dashboard/free-tiers"],
             ["Use with Claude Code", "<font name='Mono'>omniroute launch</font>"],
             ["Use with Cursor / Cline", "Base URL http://localhost:20128/v1 + your key + model auto"]], [62, 108])]

s += [Spacer(1, 5*mm), P("Sources", "h2")] + [P(x, "small") for x in [
      "OmniRoute README and docs, version 3.8.55: github.com/diegosouzapw/OmniRoute",
      "OmniRoute User Guide: docs/guides/USER_GUIDE.md",
      "OmniRoute Free Tiers Guide: docs/getting-started/FREE-TIERS-GUIDE.md",
      "OmniRoute Claude Code configuration: docs/guides/CLAUDE-CODE-CONFIGURATION.md",
      "Provider limits quoted from OmniRoute's catalog as of November 2026. Always confirm on each provider's own website.",
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
