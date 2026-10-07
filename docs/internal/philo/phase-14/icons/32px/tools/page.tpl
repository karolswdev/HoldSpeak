<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The 32 px Set</title>
<style>
:root {
  --bg: #15171d; --surface: #1c1f27; --text: #f2f3f5; --muted: #9ba2b0; --rule: #2a2e36;
  --accent: #da9868; --accent-ink: #8a5a3d;
  --desk: #3c4454; --dither: #363e4d; --steel: #9ea4b0; --ink: #0b0c10;
  --mono: ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) { --bg: #eef0f3; --surface: #ffffff; --text: #0b0c10; --muted: #4a505c; --rule: #c9cdd4; --accent: #8a5a3d; }
}
:root[data-theme="dark"] { --bg: #15171d; --surface: #1c1f27; --text: #f2f3f5; --muted: #9ba2b0; --rule: #2a2e36; }
:root[data-theme="light"] { --bg: #eef0f3; --surface: #ffffff; --text: #0b0c10; --muted: #4a505c; --rule: #c9cdd4; --accent: #8a5a3d; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.45 system-ui, sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font: 700 22px/1.2 var(--mono); margin: 0 0 4px; }
p { margin: 4px 0; color: var(--muted); max-width: 76ch; }
.call { background: var(--accent-ink); color: #fff; padding: 12px 16px; margin: 16px 0 24px; font: 700 14px/1.4 var(--mono); }
.call span { font-weight: 400; opacity: .9; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; min-width: 720px; }
th, td { border-bottom: 1px solid var(--rule); padding: 8px; vertical-align: top; text-align: center; }
thead th { font: 700 13px var(--mono); }
thead th small { display: block; font-weight: 400; color: var(--muted); }
tbody th { text-align: left; font: 700 13px var(--mono); width: 220px; }
.dk { width: 132px; height: 80px; margin: 0 auto; display: flex; gap: 12px; align-items: center; justify-content: center;
  background: var(--desk) repeating-conic-gradient(var(--dither) 0 25%, transparent 0 50%) 0 0 / 4px 4px; }
.st { width: 132px; height: 44px; margin: 0 auto; display: grid; place-items: center; background: var(--steel); }
img { image-rendering: pixelated; display: block; }
td.is-pick .dk, td.is-pick .st { outline: 2px solid var(--accent); outline-offset: -2px; }
.pick { font: 700 11px var(--mono); color: var(--accent); margin-top: 4px; }
.none { width: 132px; height: 124px; margin: 0 auto; display: grid; place-items: center; background: var(--desk); color: #c9cdd4; font: 12px var(--mono); }
.cap { font: 400 11px/1.35 var(--mono); color: var(--muted); margin-top: 4px; }
@media (max-width: 720px) { table { min-width: 600px; } th, td { padding: 4px 2px; } tbody th { width: 120px; } .dk, .st, .none { width: 110px; } }
</style>
</head>
<body>
<main>
<h1>The 32 px set: drawn at 32</h1>
<p>PHILO Phase 14, lane A0c. The list rows (ObjectList, Needs you, the confirm line, the PR card) showed the 64 px D1 icons scaled to 32, so the pixel art lost pixels. Each kind is now drawn at 32 by PixelLab, from a 2x2 seed of its 64 px icon: same silhouette, same palette, less detail, a 1 px dark outline, a transparent ground.</p>
<div class="call">RULED by Muad'Dib, 2026-10-07: the picks below. <span>Pick by fidelity to the 64 px silhouette, then by legibility on the dark Dock and the light screen. 18 base sprites (the 17 kinds plus <code>cartridge</code>, which the capability kinds wear).</span></div>
<p>Each cell: the dark desk ground at 1:1 (32 px) and at 2x, then the light steel screen at 1:1. The first column at 1:1 is what a list row showed before; at 2x it is the 64 px icon itself.</p>
<div class="scroll">
<table>
<thead><tr><th>Kind</th><th>Before<small>the 64 at 32 / the 64</small></th><th>Seed<small>2x2 box, alpha cut 50%</small></th><th>e1<small>edit, seed 1</small></th><th>e2<small>edit, seed 2</small></th></tr></thead>
<tbody>
{{ROWS}}
</tbody>
</table>
</div>
</main>
</body>
</html>
