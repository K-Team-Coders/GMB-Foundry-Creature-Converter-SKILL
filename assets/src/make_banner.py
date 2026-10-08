#!/usr/bin/env python3
"""Generates every banner from logo.png:

  assets/banner.svg                                  animated colored ASCII for the README
  assets/banner.txt                                  plain-text version
  skills/gmb-foundry-creature-converter/scripts/banner.py    terminal banner (truecolor/256/plain)
  skills/gmb-foundry-creature-converter/scripts/banner.ansi  pre-rendered for install.sh / install.ps1

The GEEK logo is rebuilt from the words "GEEK#METAVERSE#BOTS", titles from JSON
brackets — because that is literally what the tool produces.

Run from the repo root:  python assets/src/make_banner.py      (needs Pillow)
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
SKILL_SCRIPTS = ROOT / "skills" / "gmb-foundry-creature-converter" / "scripts"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CELL = 0.52  # monospace cell width / line height
LOGO_FILL = "GEEK#METAVERSE#BOTS#"
SITE = "geek-metaverse-bots.ru"
BOT = "t.me/GeekDungeonMasterBot"


# --------------------------------------------------------------------------
# bitmap -> characters
# --------------------------------------------------------------------------
def to_rows(img, cols=None, rows=None, fill="#", threshold=170, trim=True):
    w, h = img.size
    if cols is None:
        cols = max(1, round(rows * w / (h * CELL)))
    if rows is None:
        rows = max(1, round(cols * (h / w) * CELL))
    small = img.convert("L").resize((cols, rows), Image.LANCZOS)
    out, k = [], 0
    for y in range(rows):
        line = ""
        for x in range(cols):
            if small.getpixel((x, y)) > threshold:
                line += fill[k % len(fill)]
                k += 1
            else:
                line += " "
        out.append(line)
    if trim:  # drop near-empty edge rows (overshoot of round glyphs)
        dens = [len(r.replace(" ", "")) for r in out]
        while out and dens[0] < 0.2 * max(dens):
            out.pop(0); dens.pop(0)
        while out and dens[-1] < 0.2 * max(dens):
            out.pop(); dens.pop()
    return out


def text_img(text, size=120):
    font = ImageFont.truetype(FONT_BOLD, size)
    l, t, r, b = font.getbbox(text)
    img = Image.new("L", (r - l + 8, b - t + 8), 0)
    ImageDraw.Draw(img).text((4 - l, 4 - t), text, font=font, fill=255)
    return img


def logo_img():
    return Image.open(ASSETS / "logo.png").convert("L").crop((238, 212, 948, 935))


# --------------------------------------------------------------------------
# SVG for the README
# --------------------------------------------------------------------------
def make_svg():
    logo_rows = to_rows(logo_img(), cols=72, fill=LOGO_FILL)
    titles = [("GMB FOUNDRY", "url(#arcane)", "{}[]"),
              ("CREATURE", "url(#fire)", "[]{}"),
              ("CONVERTER", "url(#fire)", "{}[]")]
    W, H = 1280, 640
    lfs, llh = 10.4, 11.2
    lx, ly = 50, 100
    tx, tw = 548, 670          # title column x and max width
    trows = 8

    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GMB Foundry Creature Converter — Geek Metaverse Bots">
<defs>
  <linearGradient id="fire" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1280" y2="300" spreadMethod="reflect">
    <stop offset="0" stop-color="#ffd23f"/><stop offset="0.25" stop-color="#ff7a3d"/>
    <stop offset="0.5" stop-color="#ff2e63"/><stop offset="0.75" stop-color="#a855f7"/>
    <stop offset="1" stop-color="#22d3ee"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0; 640 0; 0 0" dur="12s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="ember" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="300" y2="540" spreadMethod="reflect">
    <stop offset="0" stop-color="#ffe066"/><stop offset="0.35" stop-color="#ff7a3d"/>
    <stop offset="0.65" stop-color="#ff2e63"/><stop offset="1" stop-color="#a855f7"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0; 0 140; 0 0" dur="7s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="arcane" gradientUnits="userSpaceOnUse" x1="548" y1="0" x2="1240" y2="0">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="0.5" stop-color="#a855f7"/><stop offset="1" stop-color="#ff2e63"/>
  </linearGradient>
  <radialGradient id="bg" cx="0.3" cy="0.4" r="0.9">
    <stop offset="0" stop-color="#1b1430"/><stop offset="1" stop-color="#07060c"/>
  </radialGradient>
  <filter id="glow" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <style>
    .m {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", "Liberation Mono", monospace; white-space: pre; }}
    .dim {{ fill: #6b6385; }} .ok {{ fill: #4ade80; }} .cmd {{ fill: #e9e4ff; }} .arrow {{ fill: #ffd23f; }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .flicker {{ animation: flick 4s ease-in-out infinite; }}
    @keyframes flick {{ 0%,100% {{ opacity: 1; }} 45% {{ opacity: .86; }} 50% {{ opacity: 1; }} 70% {{ opacity: .93; }} }}
  </style>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="#2c2448" stroke-width="2"/>
<rect x="1" y="1" width="{W-2}" height="44" rx="17" fill="#141022"/>
<rect x="1" y="30" width="{W-2}" height="15" fill="#141022"/>
<circle cx="30" cy="23" r="7" fill="#ff5f57"/><circle cx="54" cy="23" r="7" fill="#febc2e"/><circle cx="78" cy="23" r="7" fill="#28c840"/>
<text x="640" y="28" text-anchor="middle" class="m dim" font-size="14">geek@metaverse-bots: ~/GMB-Foundry-Creature-Converter</text>
''']

    def block(rows, x, y, fs, lh, cw, fill, cls=""):
        out = [f'<g class="m {cls}" font-size="{fs:.1f}" fill="{fill}" filter="url(#glow)" text-anchor="middle">']
        for i, row in enumerate(rows):
            xs = [f"{x + (j + 0.5) * cw:.1f}" for j, ch in enumerate(row) if ch != " "]
            chars = "".join(ch for ch in row if ch != " ")
            if chars:
                out.append(f'<text x="{" ".join(xs)}" y="{y + i * lh:.1f}">{escape(chars)}</text>')
        out.append("</g>")
        return "\n".join(out)

    svg.append(block(logo_rows, lx, ly, lfs, llh, llh * CELL, "url(#ember)", "flicker"))
    y = 92
    for text, fill, chars in titles:
        rows = to_rows(text_img(text), rows=trows + 1, fill=chars, threshold=130)
        cols = max(len(r) for r in rows)
        lh = min(10.6, tw / (cols * CELL))
        svg.append(block(rows, tx, y, lh * 0.94, lh, lh * CELL, fill))
        y += (len(rows) + 1.3) * lh

    ty = y + 26
    term = [
        '<tspan class="arrow">$</tspan> <tspan class="cmd">claude "перегони статблок нотика в Foundry"</tspan>',
        '<tspan class="ok">  ✓</tspan><tspan class="dim"> статблок прочитан  </tspan><tspan class="ok">✓</tspan><tspan class="dim"> JSON собран  </tspan><tspan class="ok">✓</tspan><tspan class="dim"> проверено</tspan>',
        '<tspan class="arrow">  ➜</tspan> <tspan class="cmd">fvtt-Actor-nothic.json</tspan><tspan class="dim">  · готов к Import Data</tspan>',
        '<tspan class="arrow">$</tspan> <tspan class="cursor cmd">▌</tspan>',
    ]
    for i, t in enumerate(term):
        svg.append(f'<text x="{tx}" y="{ty + i * 30:.1f}" class="m" font-size="18" xml:space="preserve">{t}</text>')
    svg.append(f'<text x="{W/2}" y="{H-24}" text-anchor="middle" class="m dim" font-size="14">'
               f'Geek Metaverse Bots  ·  {SITE}  ·  D&amp;D 5e  ·  Foundry VTT v13–v14  ·  Claude  ·  Codex</text>')
    svg.append("</svg>")
    (ASSETS / "banner.svg").write_text("\n".join(svg), encoding="utf-8")
    plain = [r.rstrip() for r in logo_rows]
    for text, _, chars in titles:
        plain += [""] + [r.rstrip() for r in to_rows(text_img(text), rows=trows + 1, fill=chars)]
    (ASSETS / "banner.txt").write_text("\n".join(plain) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# terminal banner (fits in 80 columns)
# --------------------------------------------------------------------------
BANNER_PY = r'''#!/usr/bin/env python3
"""Colored ASCII banner of GMB Foundry Creature Converter (by Geek Metaverse Bots).

    python banner.py            show it
    python banner.py --plain    without colors

Shown automatically once — the first time a script runs in a real terminal.
Respects NO_COLOR. Generated by assets/src/make_banner.py; edit that, not this.
"""
import os
import sys
from pathlib import Path

LOGO = __LOGO__
TITLE = __TITLE__
TEXT = __TEXT__
GAP = 3

# gradients (r, g, b) stops
EMBER = [(255, 224, 102), (255, 122, 61), (255, 46, 99), (168, 85, 247)]
ARCANE = [(34, 211, 238), (168, 85, 247), (255, 46, 99)]


def _lerp(stops, t):
    t = max(0.0, min(1.0, t)) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    f = t - i
    a, b = stops[i], stops[i + 1]
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def _mode():
    if os.environ.get("NO_COLOR") or "--plain" in sys.argv:
        return "plain"
    ct = os.environ.get("COLORTERM", "").lower()
    if "truecolor" in ct or "24bit" in ct or os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") in ("vscode", "iTerm.app", "WezTerm"):
        return "true"
    return "256"


def _fg(rgb, mode):
    if mode == "plain":
        return ""
    r, g, b = rgb
    if mode == "true":
        return f"\033[38;2;{r};{g};{b}m"
    idx = 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)
    return f"\033[38;5;{idx}m"


def render(mode=None):
    mode = mode or _mode()
    reset = "" if mode == "plain" else "\033[0m"
    bold = "" if mode == "plain" else "\033[1m"
    dim = "" if mode == "plain" else "\033[2m"
    lw = max(len(r) for r in LOGO)
    right = [("title", r) for r in TITLE] + [("blank", "")] + [("text", t) for t in TEXT]
    pad = max(0, (len(LOGO) - len(right)) // 2)
    right = [("blank", "")] * pad + right
    tw = max(len(r) for r in TITLE)
    lines = []
    for i in range(max(len(LOGO), len(right))):
        out = ""
        row = LOGO[i] if i < len(LOGO) else ""
        for j, ch in enumerate(row.ljust(lw)):
            out += ch if ch == " " else _fg(_lerp(EMBER, (i / max(1, len(LOGO) - 1)) * 0.75 + (j / lw) * 0.25), mode) + ch
        out += reset + " " * GAP
        kind, txt = right[i] if i < len(right) else ("blank", "")
        if kind == "title":
            for j, ch in enumerate(txt):
                out += ch if ch == " " else _fg(_lerp(ARCANE, j / max(1, tw - 1)), mode) + ch
            out += reset
        elif kind == "text":
            style, s = txt
            if style == "head":
                out += bold
                for j, ch in enumerate(s):
                    out += _fg(_lerp(EMBER, j / max(1, len(s) - 1)), mode) + ch
            elif style == "dim":
                out += dim + s
            else:
                out += s
            out += reset
        lines.append(out.rstrip())
    return "\n".join(lines) + "\n"


def _enable_windows_ansi():
    if os.name == "nt":
        os.system("")  # turns on VT processing in the Windows console


def show(stream=sys.stdout):
    _enable_windows_ansi()
    try:
        stream.write(render())
    except UnicodeEncodeError:
        stream.write(render("plain").encode("ascii", "replace").decode())
    stream.flush()


def _marker():
    base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base or Path.home()) / "gmb-foundry-creature-converter" / "welcome-shown"


def maybe_show_first_run(stream=sys.stderr):
    """Show the banner once, only to a human at a terminal (never inside agents/pipes)."""
    try:
        if not stream.isatty() or os.environ.get("CI"):
            return
        m = _marker()
        if m.exists():
            return
        show(stream)
        m.parent.mkdir(parents=True, exist_ok=True)
        m.write_text("1", encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    show()
'''


def make_terminal():
    logo = to_rows(logo_img(), cols=30, fill=LOGO_FILL)
    title = to_rows(text_img("GMB"), rows=8, fill="{}[]", threshold=140)
    text = [
        ("head", "FOUNDRY · CREATURE · CONVERTER"),
        ("norm", "статблок ➜ JSON для Foundry VTT"),
        ("blank", ""),
        ("dim", "by Geek Metaverse Bots"),
        ("norm", f"🌐 {SITE}"),
        ("norm", f"🎲 {BOT}"),
    ]
    code = (BANNER_PY.replace("__LOGO__", json.dumps(logo, ensure_ascii=False, indent=4))
                     .replace("__TITLE__", json.dumps(title, ensure_ascii=False, indent=4))
                     .replace("__TEXT__", repr([tuple(t) for t in text])))
    out = SKILL_SCRIPTS / "banner.py"
    out.write_text(code, encoding="utf-8")
    ns = {"__name__": "gen"}
    exec(compile(code, str(out), "exec"), ns)
    (SKILL_SCRIPTS / "banner.ansi").write_text(ns["render"]("true"), encoding="utf-8")
    (SKILL_SCRIPTS / "banner.txt").write_text(ns["render"]("plain"), encoding="utf-8")
    return max(len(l) for l in ns["render"]("plain").splitlines())


def main():
    make_svg()
    w = make_terminal()
    print(f"wrote banner.svg, banner.txt, scripts/banner.py (+ .ansi/.txt, {w} cols)")


if __name__ == "__main__":
    main()
