<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Icon Mold</title>
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
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.45 system-ui, sans-serif; }
main { max-width: 1240px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font: 700 22px/1.2 var(--mono); margin: 0 0 4px; }
h2 { font: 700 16px/1.2 var(--mono); margin: 40px 0 8px; }
p { margin: 4px 0; color: var(--muted); max-width: 72ch; }
.call { position: sticky; top: 0; z-index: 2; background: var(--accent-ink); color: #fff; padding: 12px 16px; margin: 16px 0 24px; font: 700 14px/1.4 var(--mono); box-shadow: inset 1px 1px 0 rgba(255,255,255,.36), inset -1px -1px 0 rgba(0,0,0,.25); }
.call span { font-weight: 400; opacity: .9; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; min-width: 760px; }
th, td { border-bottom: 1px solid var(--rule); padding: 8px; vertical-align: top; text-align: center; }
thead th { font: 700 13px var(--mono); }
thead th small { display: block; font-weight: 400; color: var(--muted); }
tbody th { text-align: left; font: 700 13px var(--mono); width: 150px; }

.dk { width: 88px; height: 80px; margin: 0 auto; display: grid; place-items: center;
  background: var(--desk) repeating-conic-gradient(var(--dither) 0 25%, transparent 0 50%) 0 0 / 4px 4px; }
.st { width: 88px; height: 44px; margin: 0 auto; display: grid; place-items: center; background: var(--steel); }
img { image-rendering: pixelated; display: block; }
.none { width: 88px; height: 124px; margin: 0 auto; display: grid; place-items: center; background: var(--desk); color: #c9cdd4; font: 12px var(--mono); }
.cap { font: 11px/1.3 var(--mono); color: var(--muted); max-width: 150px; margin: 4px auto 0; }
.situ { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-start; margin-bottom: 8px; }
.situ figure { margin: 0; }
.situ img.l { width: 900px; max-width: 100%; height: auto; }
.situ img.r { width: 280px; max-width: 100%; height: auto; }
@media (max-width: 720px) { table { min-width: 460px; } th, td { padding: 4px 2px; } tbody th { width: 80px; font-size: 12px; } .dk, .st, .none { width: 72px; } .cap { font-size: 10px; } }
figcaption { font: 700 13px var(--mono); margin: 0 0 6px; }
</style>
</head>
<body>
<main>
<h1>The icon mold: three directions</h1>
<p>PHILO Phase 14, lane A0. Seventeen kinds, three styles, made on PixelLab. Each row shows the sprite at 64 px on the desk and at 32 px on the steel screen (the 393 list row). The code under each icon is its PixelLab object id.</p>
<p>Nothing in the product changed. The current column is the mold in <code>web/public/desk/sprites</code> today.</p>

<div class="call">Your call: D1, D2 or D3, or a mix <span>(example: "D1, but D2's documents")</span></div>

<div class="scroll">
<table>
<thead><tr><th scope="col">Kind</th><th scope="col">Current<small>the mold today</small></th><th scope="col">D1 Workbench+<small>steel, bevel, one ember</small></th><th scope="col">D2 Signal objects<small>flat, two-tone, front</small></th><th scope="col">D3 Tactile desk<small>wood, brass, paper</small></th></tr></thead>
<tbody>
{{ROWS}}
</tbody>
</table>
</div>

<h2>On the desk (board A-1, the top-left region, 1:1 at 1440)</h2>
<p>The A-1 board with each direction pasted over its sprites. Counts and lamps are the board's own. The right strip is Claude Code, Needs you and Parked from the right edge. The note and memory have no icon on this board.</p>
<div class="situ"><figure><figcaption>Current</figcaption><img class="l" src="insitu/control-left.png" alt="A-1 today"></figure><figure><figcaption>&nbsp;</figcaption><img class="r" src="insitu/control-right.png" alt=""></figure></div>
<div class="situ"><figure><figcaption>D1 Workbench+</figcaption><img class="l" src="insitu/D1-left.png" alt="A-1 with D1"></figure><figure><figcaption>&nbsp;</figcaption><img class="r" src="insitu/D1-right.png" alt=""></figure></div>
<div class="situ"><figure><figcaption>D2 Signal objects</figcaption><img class="l" src="insitu/D2-left.png" alt="A-1 with D2"></figure><figure><figcaption>&nbsp;</figcaption><img class="r" src="insitu/D2-right.png" alt=""></figure></div>
<div class="situ"><figure><figcaption>D3 Tactile desk</figcaption><img class="l" src="insitu/D3-left.png" alt="A-1 with D3"></figure><figure><figcaption>&nbsp;</figcaption><img class="r" src="insitu/D3-right.png" alt=""></figure></div>
</main>
</body>
</html>
