"""Builds WIKI.html (a single self-contained web page) from WIKI.md.

Run from the project folder after editing WIKI.md:
    python tools/build_wiki_html.py

Needs the "markdown" package:  pip install markdown
"""
import html
import os
import re

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "WIKI.md")
OUT = os.path.join(ROOT, "WIKI.html")


def slugify(text, sep="-"):
    """GitHub-style anchors, so the [links](#world-map--floors) written in WIKI.md keep working."""
    text = re.sub(r"<[^>]+>", "", str(text)).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", sep)


CSS = """
:root {
  --bg: #0a1230; --bg2: #0e1a44; --panel: #12224f; --panel2: #182c62; --line: #3a4b80;
  --gold: #f0c462; --gold-light: #ffecb0; --text: #f4eee0; --dim: #aab3cf; --code: #0a1330;
  --blue: #8fc3ff; --side: 290px;
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --bg: #f5f1e6; --bg2: #ebe4d1; --panel: #ffffff; --panel2: #f0ead8; --line: #cfc5a8; --gold: #8a5a10;
    --gold-light: #6b4306; --text: #221d12; --dim: #6a624c; --code: #efe8d4; --blue: #1f5fa8;
  }
}
:root[data-theme="light"] {
  --bg: #f5f1e6; --bg2: #ebe4d1; --panel: #ffffff; --panel2: #f0ead8; --line: #cfc5a8; --gold: #8a5a10;
  --gold-light: #6b4306; --text: #221d12; --dim: #6a624c; --code: #efe8d4; --blue: #1f5fa8;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 24px; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.65 "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
  background-image: radial-gradient(1200px 500px at 70% -10%, var(--bg2), transparent);
  background-repeat: no-repeat;
}
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---- layout ---- */
.side {
  position: fixed; inset: 0 auto 0 0; width: var(--side); overflow-y: auto; padding: 26px 18px 40px;
  background: var(--panel); border-right: 1px solid var(--line); z-index: 20;
}
.brand { font: 700 22px/1.2 Georgia, Cambria, serif; color: var(--gold); margin: 0 6px 4px; }
.brand-sub { color: var(--dim); font-size: 13px; margin: 0 6px 18px; }
.side nav a {
  display: block; padding: 7px 12px; margin: 2px 0; border-radius: 8px; color: var(--dim); font-size: 14.5px;
  border-left: 3px solid transparent;
}
.side nav a:hover { background: var(--panel2); color: var(--text); text-decoration: none; }
.side nav a.active { background: var(--panel2); color: var(--gold-light); border-left-color: var(--gold); }
.theme-btn {
  margin: 18px 6px 0; padding: 7px 12px; width: calc(100% - 12px); background: transparent; color: var(--dim);
  border: 1px solid var(--line); border-radius: 8px; cursor: pointer; font: inherit; font-size: 13px;
}
.theme-btn:hover { color: var(--text); border-color: var(--gold); }
main { margin-left: var(--side); padding: 56px 48px 80px; }
.page { max-width: 900px; margin: 0 auto; }

/* ---- hero ---- */
.hero { padding: 6px 0 30px; border-bottom: 1px solid var(--line); margin-bottom: 8px; }
.hero h1 {
  font: 700 clamp(34px, 5vw, 52px)/1.1 Georgia, Cambria, serif; color: var(--gold); margin: 0 0 14px;
  letter-spacing: .5px;
}
.hero p { font-size: 18px; color: var(--dim); margin: 0; }

/* ---- content ---- */
h2 {
  font: 700 29px/1.25 Georgia, Cambria, serif; color: var(--gold); margin: 54px 0 14px; padding-bottom: 10px;
  border-bottom: 2px solid var(--line);
}
h3 { font: 700 19px/1.3 "Segoe UI", system-ui, sans-serif; color: var(--gold-light); margin: 30px 0 8px; }
p { margin: 10px 0; }
ul, ol { padding-left: 1.4em; margin: 10px 0; }
li { margin: 5px 0; }
li::marker { color: var(--gold); }
strong { color: var(--gold-light); }
em { color: var(--text); }
hr { border: 0; height: 1px; background: var(--line); margin: 0; opacity: .0; }
code {
  font: 0.9em/1.4 "Cascadia Mono", Consolas, "SF Mono", monospace; background: var(--code); color: var(--gold-light);
  padding: 2px 6px; border-radius: 5px; border: 1px solid var(--line);
}
pre {
  background: var(--code); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; overflow-x: auto;
  margin: 14px 0; line-height: 1.5;
}
pre code { background: none; border: 0; padding: 0; color: var(--text); font-size: 13.5px; }
.table-wrap { overflow-x: auto; margin: 16px 0; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); }
table { border-collapse: collapse; width: 100%; font-size: 15px; }
th {
  background: var(--panel2); color: var(--gold); text-align: left; font-weight: 700; white-space: nowrap;
  padding: 11px 14px; border-bottom: 2px solid var(--gold);
}
td { padding: 10px 14px; border-top: 1px solid var(--line); vertical-align: top; }
tbody tr:nth-child(even) td { background: color-mix(in srgb, var(--panel2) 45%, transparent); }
tbody tr:hover td { background: var(--panel2); }
h2 .anchor, h3 .anchor { opacity: 0; margin-left: 8px; font-size: .7em; color: var(--dim); }
h2:hover .anchor, h3:hover .anchor { opacity: 1; }
footer { margin-top: 70px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--dim); font-size: 13.5px; }

/* ---- small screens ---- */
.menu-btn {
  display: none; position: fixed; top: 12px; left: 12px; z-index: 30; padding: 9px 14px; border-radius: 10px;
  background: var(--panel); color: var(--gold); border: 1px solid var(--line); font: 600 14px "Segoe UI", sans-serif;
  cursor: pointer;
}
@media (max-width: 900px) {
  .menu-btn { display: block; }
  .side { transform: translateX(-100%); transition: transform .2s; box-shadow: 0 0 40px #0008; }
  body.open .side { transform: none; }
  main { margin-left: 0; padding: 70px 20px 60px; }
}
@media print {
  .side, .menu-btn { display: none; }
  main { margin: 0; padding: 0; }
  :root { --bg: #fff; --panel: #fff; --panel2: #eee; --text: #000; --dim: #444; --gold: #7a4b00; --gold-light: #000;
          --line: #999; --code: #f3f3f3; --blue: #003b8e; }
  body { background: #fff; }
}
"""

JS = """
(function () {
  var links = [].slice.call(document.querySelectorAll('.side nav a'));
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  function spy() {
    var y = window.scrollY + 120, cur = 0;
    heads.forEach(function (h, i) { if (h && h.offsetTop <= y) cur = i; });
    links.forEach(function (a, i) { a.classList.toggle('active', i === cur); });
  }
  window.addEventListener('scroll', spy, { passive: true }); spy();
  links.forEach(function (a) { a.addEventListener('click', function () { document.body.classList.remove('open'); }); });
  document.querySelector('.menu-btn').addEventListener('click', function () { document.body.classList.toggle('open'); });
  var root = document.documentElement, btn = document.querySelector('.theme-btn');
  try { var saved = localStorage.getItem('wiki-theme'); if (saved) root.setAttribute('data-theme', saved); } catch (e) {}
  btn.addEventListener('click', function () {
    var dark = getComputedStyle(root).getPropertyValue('--bg').trim() === '#0a1230';
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('wiki-theme', next); } catch (e) {}
  });
})();
"""


def main():
    with open(SRC, encoding="utf-8") as f:
        text = f.read()
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "toc"],
        extension_configs={"toc": {"slugify": slugify, "permalink": "#", "permalink_class": "anchor"}})

    # page title and intro become the hero; the written contents list is replaced by the sidebar
    title = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    intro = re.search(r"</h1>\s*<p>(.*?)</p>", body, re.S)
    body = body.replace(title.group(0), "", 1)
    body = body.replace(f"<p>{intro.group(1)}</p>", "", 1)
    body = re.sub(r'<h2 id="table-of-contents">.*?</ul>', "", body, count=1, flags=re.S)
    body = re.sub(r"<hr\s*/?>", "", body)
    body = re.sub(r"(<table>.*?</table>)", r'<div class="table-wrap">\1</div>', body, flags=re.S)
    title_text = re.sub(r"<a [^>]*class=\"anchor\".*?</a>", "", title.group(1)).strip()

    sections = re.findall(r'<h2 id="([^"]+)">(.*?)<a ', body, re.S)
    nav = "\n".join(f'<a href="#{i}">{html.escape(html.unescape(t.strip()))}</a>' for i, t in sections)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(html.unescape(title_text))}</title>
<style>{CSS}</style>
</head>
<body>
<button class="menu-btn" type="button">&#9776; Menu</button>
<aside class="side">
  <div class="brand">Spells x Blades</div>
  <div class="brand-sub">Game wiki</div>
  <nav>
{nav}
  </nav>
  <button class="theme-btn" type="button">Toggle light / dark</button>
</aside>
<main>
  <div class="page">
    <header class="hero">
      <h1>{title_text}</h1>
      <p>{intro.group(1)}</p>
    </header>
{body}
    <footer>Generated from WIKI.md. Edit that file and run <code>python tools/build_wiki_html.py</code> to update this page.</footer>
  </div>
</main>
<script>{JS}</script>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", OUT, f"({len(sections)} sections)")


if __name__ == "__main__":
    main()
