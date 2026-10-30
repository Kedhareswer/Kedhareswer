"""Build the animated SVGs behind the profile README ("Kedhar, tokenized").

    python scripts/build.py            hero (needs Pillow, run locally)
    python scripts/build.py training   training log (stdlib only; needs GITHUB_TOKEN, run by the daily Action)

Each asset is written as assets/<name>-dark.svg and assets/<name>-light.svg for <picture>.
Animations only use "from" keyframes, so the static style is the final frame and
prefers-reduced-motion just switches them off.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
USER = "Kedhareswer"

THEMES = {
    "light": dict(paper="#f2ede3", ink="#17140f", accent="#e84500", rule="#17140f",
                  chips=["#ffd6c2", "#c9e4ff", "#d9f5c8", "#f6d3f2", "#fff1b8", "#e5e0d6"],
                  ramp="@&%#X$x+=;:-·. "),
    "dark": dict(paper="#12100d", ink="#ece5d6", accent="#ff6a2b", rule="#ece5d6",
                 chips=["#5a2e1f", "#1f3a55", "#2b4a22", "#4d2a49", "#544a1c", "#2f2b25"],
                 ramp="@&%#X$x+=;:-·. "),
}
MONO = "ui-monospace,'SF Mono','Cascadia Code',Consolas,Menlo,monospace"
EASE = "cubic-bezier(.2,.8,.2,1)"

# Hand-drawn letters on a 60x100 grid, so the name never depends on the viewer's fonts.
LETTERS = {
    "K": ["M0 0V100", "M58 0L4 54", "M22 36L60 100"],
    "E": ["M60 0H0V100H60", "M0 50H46"],
    "D": ["M0 0V100H28C50 100 60 84 60 64V36C60 16 50 0 28 0Z"],
    "H": ["M0 0V100", "M60 0V100", "M0 50H60"],
    "A": ["M0 100L30 0L60 100", "M11 64H49"],
    "R": ["M0 100V0H36C52 0 60 11 60 25S52 50 36 50H0", "M30 50L60 100"],
}

BIO = ["AI", " engineer", " &", " full", "-stack", " dev", ".", " #1", " on", " 21st", ".dev", ".",
       " builds", " agents", " that", " ship", "."]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, title, desc, css, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            f'<style>text{{font-family:{MONO}}}{css}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>{body}</svg>\n')


def frame(t, w, h, left, right):
    return (f'<rect width="{w}" height="{h}" rx="6" fill="{t["paper"]}"/>'
            f'<text x="48" y="50" font-size="14" fill="{t["ink"]}" fill-opacity=".6">{esc(left)}</text>'
            f'<text x="{w - 48}" y="50" text-anchor="end" font-size="14" fill="{t["ink"]}" fill-opacity=".6">{esc(right)}</text>'
            f'<line x1="48" y1="66" x2="{w - 48}" y2="66" stroke="{t["rule"]}" stroke-opacity=".2"/>')


def token_id(tok):
    # decorative ids, stable per token
    return int(hashlib.md5(tok.encode()).hexdigest(), 16) % 50000


def hero(t):
    from PIL import Image  # only the hero needs it; the Action never builds the hero

    W, H = 1200, 600
    ink, accent = t["ink"], t["accent"]
    # ascii portrait; the pure-red studio backdrop drops out to blank paper
    im = Image.open(ROOT / "Assests" / "me.png").convert("RGB").crop((40, 280, 640, 810))
    cols, rows, cw, chh = 64, 32, 7.9, 14
    im = im.resize((cols, rows), Image.LANCZOS)
    ramp = t["ramp"]
    lines = []
    for r in range(rows):
        row = ""
        for c in range(cols):
            R, G, B = im.getpixel((c, r))
            lum = .299 * R + .587 * G + .114 * B
            row += " " if R > 2 * G + 12 else ramp[min(len(ramp) - 1, int((lum / 200) ** .8 * (len(ramp) - 1)))]
        lines.append(row.rstrip())
    px, py = 690, 76
    css = (".row{animation:dec .5s steps(3) both}@keyframes dec{from{opacity:0}}"
           ".scr{animation:out .5s steps(3) both}@keyframes out{to{opacity:0}}"
           f".scan{{animation:scan 5s {EASE} 2.4s infinite both}}"
           f"@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({rows * chh}px)}}}}"
           f".chip{{animation:chip .45s {EASE} both}}@keyframes chip{{from{{opacity:0;transform:translateY(14px)}}}}"
           ".ltr{stroke-dasharray:1;animation:draw 1s ease-out both}@keyframes draw{from{stroke-dashoffset:1}}"
           ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
    body = [frame(t, W, H, "FIG. 01 — SELF, TOKENIZED", "kedhar.vercel.app")]
    junk = "!<>[]{}/\\|=+*^?#_01"
    seed = 5
    for r, row in enumerate(lines):
        y = py + 20 + r * chh
        d = .35 + r * .045
        scr = ""
        for ch in row:
            seed = (seed * 1103515245 + 12345) % 2 ** 31
            scr += " " if ch == " " else junk[seed % len(junk)]
        tl = f'textLength="{len(row) * cw:.1f}" lengthAdjust="spacingAndGlyphs"' if row.strip() else ""
        body.append(f'<text class="scr" x="{px}" y="{y}" font-size="12.5" fill="{accent}" xml:space="preserve" {tl} '
                    f'style="animation-delay:{d:.2f}s">{esc(scr)}</text>'
                    f'<text class="row" x="{px}" y="{y}" font-size="12.5" fill="{ink}" xml:space="preserve" {tl} '
                    f'style="animation-delay:{d + .25:.2f}s">{esc(row)}</text>')
    body.append(f'<rect class="scan" x="{px - 6}" y="{py}" width="{cols * cw + 12:.0f}" height="10" fill="{accent}" fill-opacity=".4"/>')
    s, gap = .92, 20
    for i, ch in enumerate("KEDHAR"):
        x = 48 + i * (60 * s + gap)
        body += [f'<path class="ltr" d="{d}" pathLength="1" fill="none" stroke="{ink}" stroke-width="{9 / s:.2f}" '
                 f'transform="translate({x:.1f} 120) scale({s})" style="animation-delay:{i * .1:.1f}s"/>' for d in LETTERS[ch]]
    body.append(f'<text x="48" y="274" font-size="15" fill="{ink}">&gt; tokenize(<tspan fill="{accent}">"kedhar"</tspan>)'
                f'<tspan class="blink">▌</tspan></text>')
    x, y, delay = 48, 312, .9
    for k, tok in enumerate(BIO):
        w = max(len(tok), 2) * 9.4 + 14
        if x + w > 640:
            x, y = 48, y + 62
        body.append(f'<g class="chip" style="animation-delay:{delay:.2f}s">'
                    f'<rect x="{x}" y="{y}" width="{w:.0f}" height="30" rx="5" fill="{t["chips"][k % 6]}"/>'
                    f'<text x="{x + 7}" y="{y + 20}" font-size="15" fill="{ink}" xml:space="preserve">{esc(tok)}</text>'
                    f'<text x="{x + 7}" y="{y + 46}" font-size="11" fill="{ink}" fill-opacity=".5">{token_id(tok)}</text></g>')
        x += w + 6
        delay += .12
    body.append(f'<text x="48" y="{H - 44}" font-size="14" fill="{ink}" fill-opacity=".6">'
                f'{len(BIO)} TOKENS · AI ENGINEER &amp; FULL-STACK DEVELOPER · MADANAPALLI, IN</text>')
    return svg(W, H, "Kedhar, tokenized",
               "An ASCII portrait of Kedhar decodes from scrambled characters while a scan line passes over it. "
               "Beside it the name KEDHAR draws itself and his bio appears as tokenizer chips: " + "".join(BIO),
               css, "".join(body))


# ---------------------------------------------------------------- training log (daily Action)

def api(url, token, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_training(token, today):
    # The contribution calendar API reports 0 for this account, so count public commits via search instead.
    start = today - dt.timedelta(days=371)
    shas, counts = set(), {}
    m = dt.date(start.year, start.month, 1)
    while m <= today:
        nxt = dt.date(m.year + m.month // 12, m.month % 12 + 1, 1)
        q = f"author:{USER} committer-date:{m}..{nxt - dt.timedelta(days=1)}"
        for page in range(1, 11):  # shortcut: search caps at 1,000 commits per month; split by week if a month ever exceeds it
            res = api("https://api.github.com/search/commits?" + urllib.parse.urlencode(
                {"q": q, "per_page": 100, "page": page}), token)
            for it in res["items"]:
                if it["sha"] not in shas:
                    shas.add(it["sha"])
                    day = dt.date.fromisoformat(it["commit"]["committer"]["date"][:10])
                    counts[day] = counts.get(day, 0) + 1
            time.sleep(2.2)  # search API allows 30 requests a minute
            if len(res["items"]) < 100:
                break
        m = nxt
    repos = api("https://api.github.com/graphql", token, {"query": f"""{{user(login:"{USER}"){{repositories(
        ownerAffiliations:OWNER,privacy:PUBLIC,first:100,orderBy:{{field:STARGAZERS,direction:DESC}})
        {{totalCount nodes{{stargazerCount}}}}}}}}"""})["data"]["user"]["repositories"]
    return {"counts": {d.isoformat(): n for d, n in sorted(counts.items())}, "repos": repos["totalCount"],
            "stars": sum(n["stargazerCount"] for n in repos["nodes"]), "today": today.isoformat()}


def streaks(counts, today):
    cur = 0
    d = today if counts.get(today) else today - dt.timedelta(days=1)  # today may still be empty
    while counts.get(d):
        cur, d = cur + 1, d - dt.timedelta(days=1)
    best = run = 0
    for i in range(365, -1, -1):
        run = run + 1 if counts.get(today - dt.timedelta(days=i)) else 0
        best = max(best, run)
    return cur, best


def training(t, data):
    today = dt.date.fromisoformat(data["today"])
    counts = {dt.date.fromisoformat(k): v for k, v in data["counts"].items()}
    first = today - dt.timedelta(days=today.isoweekday() % 7 + 52 * 7)  # Sunday, 53 columns ago
    W, H, cw, ch, gx, gy = 1200, 330, 14.6, 22, 48, 118
    glyphs = [(0, "·", .18), (1, ":", .5), (3, "+", .75), (6, "x", 1), (10, "#", 1)]
    css = (".c{animation:fade .4s ease-out both}@keyframes fade{from{opacity:0}}"
           f".scan{{animation:scan 9s linear 2s infinite both}}@keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX({53 * cw:.0f}px)}}}}")
    body = [frame(t, W, H, "FIG. 02 — TRAINING LOG · PUBLIC COMMITS, LAST 12 MONTHS", f"updated {today}")]
    year = sum(n for d, n in counts.items() if d >= first)
    for col in range(53):
        cells = []
        for row in range(7):
            d = first + dt.timedelta(days=col * 7 + row)
            if d > today:
                break
            n = counts.get(d, 0)
            g, o = next((g, o) for lo, g, o in reversed(glyphs) if n >= lo)
            fill = t["accent"] if g == "#" else t["ink"]
            cells.append(f'<text x="{gx + col * cw:.1f}" y="{gy + row * ch}" font-size="15" fill="{fill}" fill-opacity="{o}">{g}</text>')
        if (first + dt.timedelta(days=col * 7)).day <= 7:
            mon = (first + dt.timedelta(days=col * 7)).strftime("%b").upper()
            cells.append(f'<text x="{gx + col * cw:.1f}" y="{gy - 26}" font-size="12" fill="{t["ink"]}" fill-opacity=".5">{mon}</text>')
        body.append(f'<g class="c" style="animation-delay:{col * .025:.3f}s">{"".join(cells)}</g>')
    body.append(f'<rect class="scan" x="{gx - 3}" y="{gy - 16}" width="{cw:.0f}" height="{7 * ch}" fill="{t["accent"]}" fill-opacity=".12"/>')
    cur, best = streaks(counts, today)
    stats = [(f"{year:,}", "commits"), (f"{cur}d", "current streak"), (f"{best}d", "longest streak"), (f"{data['stars']}", "stars")]
    for k, (v, label) in enumerate(stats):
        x, y = 880 + (k % 2) * 150, 128 + (k // 2) * 82
        body += [f'<text x="{x}" y="{y}" font-size="30" font-weight="700" fill="{t["accent"] if k == 0 else t["ink"]}">{v}</text>',
                 f'<text x="{x}" y="{y + 22}" font-size="12" letter-spacing="1" fill="{t["ink"]}" fill-opacity=".6">{label.upper()}</text>']
    legend = "  ".join(f"{g} {lo}+" for lo, g, _ in glyphs[1:])
    body.append(f'<text x="{gx}" y="{H - 40}" font-size="13" fill="{t["ink"]}" fill-opacity=".6">· none   {legend}   '
                f'· {data["repos"]} public repos</text>')
    return svg(W, H, "Training log", f"Public commits over the last 12 months drawn as a grid of characters: {year} commits, "
               f"current streak {cur} day{'s' * (cur != 1)}, longest streak {best} day{'s' * (best != 1)}, {data['stars']} stars, {data['repos']} public repos.",
               css, "".join(body))


def write(name, fn, *args):
    OUT.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        (OUT / f"{name}-{theme}.svg").write_text(fn(t, *args), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["training"]:
        write("training", training, fetch_training(os.environ["GITHUB_TOKEN"], dt.datetime.now(dt.timezone.utc).date()))
    else:
        write("hero", hero)
    print("done")
