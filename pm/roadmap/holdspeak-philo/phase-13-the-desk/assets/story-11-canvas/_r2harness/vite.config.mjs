// PHILO-13-11 (C1) canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME (the Phase 10/11/12 method,
// ../../../../phase-12-send-from-the-floor/assets/story-02-canvas/harness/).
//
//   CANVAS_MODE=proposal:
//     - canvas.css: THE PROPOSED MATERIAL (the Workbench tokens and the chrome
//       rules the build moves into tokens.css / window-chrome.css / pullout.css /
//       dock.css / chrome-menus.css / chair.css), loaded AFTER the app's CSS;
//     - SEATS: each product file the look touches gets ONE named hook into
//       harness/p13.tsx at a NAMED anchor (the SEATS table). A missing or doubled
//       anchor STOPS THE SERVER: the canvas never draws a seat the product file
//       does not have. With p13.tsx absent each hook is a no-op;
//     - p13.tsx: the proposed composition (the gadget set, the screen title bar,
//       the Chair as windows, the AppIcons, the Parked face) and the stand-in
//       data the build does not have yet (stated in its header).
//   CANVAS_MODE=today: the product exactly as on this branch, no seat, no shim.
// HUB = the real hub's origin (rig.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";
import { existsSync } from "node:fs";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48902";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";
const G = "(globalThis as any)";

/** [product file (suffix), import line or null, [[anchor, replacement, count?], ...]] */
const SEATS = [
  // (1) The gadget set: close at the left; iconify, zoom and depth at the right;
  // the sizing gadget in the bottom-right corner. ONE composition for every
  // DeskWindowFrame host (19 host files).
  ["src/desk/components/DeskWindow.tsx", null, [
    ["        <span className=\"desk-traffic\">",
      `        {${G}.__p13Gadgets ? ${G}.__p13Gadgets("left", { id, name, compact, maximized, requestClose, requestMinimize }) : null}\n        <span className="desk-traffic" data-p13-today="" hidden={Boolean(${G}.__p13Gadgets)}>`],
    ["        {actions ? <span className=\"desk-window-actions\">{actions}</span> : null}\n      </header>",
      `        {actions ? <span className="desk-window-actions">{actions}</span> : null}\n        {${G}.__p13Gadgets ? ${G}.__p13Gadgets("right", { id, name, compact, maximized, requestClose, requestMinimize }) : null}\n      </header>`],
    // (C1-2) right button anywhere in the head: the window's menu with the Amiga-key column.
    ["          entries={headMenuEntries({",
      `          entries={(${G}.__p13HeadMenu ?? ((_i: string, _n: string, e: unknown) => e))(id, name, headMenuEntries({`],
    ["            requestClose,\n          })}\n          onClose={() => setHeadMenu(null)}",
      "            requestClose,\n          }))}\n          onClose={() => setHeadMenu(null)}"],
  ]],
  // (2) The screen title bar: the front window's name, beside the menus.
  ["src/desk/components/DeskChrome.tsx", null, [
    ["        <DeskMenuBar />\n",
      `        <DeskMenuBar />\n        {${G}.__p13ScreenTitle ? ${G}.__p13ScreenTitle() : null}\n`],
  ]],
  // (4) The Chair composed of windows: the Arrival's real sections, each routed
  // into one of the Chair's windows (Needs you, Brief, The week, Capture).
  ["src/desk/chair/ChairHome.tsx", null, [
    ["  return (\n    <>\n      {/* ── Headline ── */}",
      `  const P13Chair = ${G}.__p13ChairDesk ?? ((p: { children: React.ReactNode }) => <>{p.children}</>);\n  return (\n    <P13Chair>\n      {/* ── Headline ── */}`],
    ["      <CaptureBar />\n    </>\n  );\n}",
      "      <CaptureBar />\n    </P13Chair>\n  );\n}"],
  ]],
  // (7) The AppIcons: live state drawn on the icon (stand-in values until C3).
  ["src/desk/components/window/Dock.tsx", null, [
    ["            <span className=\"desk-dock-label\">{application.label}</span>\n            {badge ? (",
      `            <span className="desk-dock-label">{application.label}</span>\n            {${G}.__p13AppState ? ${G}.__p13AppState(application.windowId) : null}\n            {badge ? (`],
    ["      <RoomActions />\n",
      `      <RoomActions />\n      {${G}.__p13AppIcons ? ${G}.__p13AppIcons() : null}\n`],
  ]],
  // (A1-F) "Parked and Restore" on Meetings: Park replaces Delete (no confirm: it is
  // undone by Restore); the PARKED token and the parked rows; the PARKED receipt.
  ["src/pages/cores/HistoryCore.tsx", null, [
    ["  const [receipt, setReceipt] = useState<Receipt | null>(null);\n",
      `  const [receipt, setReceipt] = useState<Receipt | null>(null);\n  ${G}.__p13UseTick?.();\n`],
    ["      meetingRows={meetingRows}\n",
      `      meetingRows={${G}.__p13Unparked ? ${G}.__p13Unparked("meetings", meetingRows) : meetingRows}\n`],
    ["      {/* The stream + detail split */}\n",
      `      {${G}.__p13ParkedStrip ? ${G}.__p13ParkedStrip("meetings") : null}\n      {/* The stream + detail split */}\n`],
    ["              <ConfirmVerb\n                label=\"Delete\"\n                confirmLabel=\"Delete?\"\n                busy={removing}\n                onConfirm={() => void removeSelected()}\n              />",
      `              {${G}.__p13ParkVerb ? ${G}.__p13ParkVerb("meetings", selected, () => setSelected(null)) : <ConfirmVerb\n                label="Delete"\n                confirmLabel="Delete?"\n                busy={removing}\n                onConfirm={() => void removeSelected()}\n              />}`],
    ["          main={rail}\n",
      `          main={${G}.__p13ParkedOn?.("meetings") ? null : rail}\n`],
    ["        receipt={\n          <span\n            className=\"surface-footer-receipt-line\"",
      `        receipt={${G}.__p13Receipt?.("meetings") ??\n          <span\n            className="surface-footer-receipt-line"`],
    ["countToken(meetingRows.length, \"RECORD\")",
      `countToken((${G}.__p13Unparked ? ${G}.__p13Unparked("meetings", meetingRows, true) : meetingRows).length, "RECORD")`],
  ]],
  // (A1-F) on the Workbench window: Remove parks the item; PARKED token; receipt.
  ["src/desk/components/WorkbenchWindow.tsx", null, [
    ["  const { remove, receipt: undoReceipt, phase: undoPhase } = useUndoReceipt();\n",
      `  const { remove, receipt: undoReceipt, phase: undoPhase } = useUndoReceipt();\n  ${G}.__p13UseTick?.();\n`],
    ["  const handleRemove = (item: WorkbenchItem) => {\n",
      `  const handleRemove = (item: WorkbenchItem) => {\n    if (${G}.__p13Park?.("workbench", item)) return;\n`],
    ["              {items.map((item) => (\n                <WorkbenchItemCard",
      `              {${G}.__p13ParkedStrip ? ${G}.__p13ParkedStrip("workbench") : null}\n              {(${G}.__p13Unparked ? ${G}.__p13Unparked("workbench", items) : items).map((item: WorkbenchItem) => (\n                <WorkbenchItemCard`],
    ["          (undoPhase === \"pending\" || undoPhase === \"committing\" ? undoReceipt : null) ||",
      `          (${G}.__p13Receipt ? ${G}.__p13Receipt("workbench") : null) ||\n          (undoPhase === "pending" || undoPhase === "committing" ? undoReceipt : null) ||`],
  ]],
  // (A2, drawn fixed) ONE meaning of "needs you" (story 03: R1 ranked rows + R2 blockers + R3 failed
  // summaries). The Chair publishes its count; the bell, the Dock and the Desk memory icon read it;
  // narrower counts say what they count.
  ["src/desk/chair/ChairHome.tsx#needs", null, [
    ["  const headlineAccent = count > 0 || pending > 0;\n",
      `  const headlineAccent = count > 0 || pending > 0;\n  ${G}.__p13PublishNeedsYou?.(count + pending);\n`],
    ["  const label = muted ? \"MUTED\" : \"NEEDS YOU\";",
      `  const label = muted ? "MUTED" : (${G}.__p13 ? "ACTIONS" : "NEEDS YOU");`],
  ]],
  ["src/desk/components/DeskChrome.tsx#bell", null, [
    ["  const attention = launchers.find((l) => l.id === \"attention\");\n",
      `  const attention = launchers.find((l) => l.id === "attention");\n  const __p13N = ${G}.__p13UseNeedsYou?.();\n`],
    ["  const badge = (attention.badge ?? 0) + heldCount;",
      "  const badge = __p13N ?? (attention.badge ?? 0) + heldCount;"],
    ["          ? `Desk memory: ${badge} need attention`",
      "          ? `Desk memory: ${badge} need you`"],
  ]],
  ["src/desk/components/window/Dock.tsx#needs", null, [
    ["  const intelligenceBadge = needsYouCount > 0\n    ? String(needsYouCount)",
      `  const __p13N: number = ${G}.__p13UseNeedsYou?.() ?? needsYouCount;\n  const intelligenceBadge = __p13N > 0\n    ? String(__p13N)`],
    ["`${badge} overdue`", "`${badge} need you`"],
    ["  const shown = launchers.filter((l) => !windows.some((w) => w.id === l.id));",
      `  const shown = launchers.map((l) => (${G}.__p13 && l.id === "attention" ? { ...l, badge: __p13N } : l)).filter((l) => !windows.some((w) => w.id === l.id));`],
  ]],
  ["src/pages/cores/history/helpers.ts", null, [
    ["  return { text: \"Nothing needs you\", accent: false };",
      `  return { text: ${G}.__p13 ? "All summaries done" : "Nothing needs you", accent: false };`],
  ]],
  ["src/features/project-room/ProjectRoomCore.tsx", null, [
    ["      {count === 1 ? \"1 needs you\" : count > 0 ? `${count} need you` : \"Nothing needs you\"}",
      `      {${G}.__p13 ? (count > 0 ? \`\${count} open here\` : "Clear here") : count === 1 ? "1 needs you" : count > 0 ? \`\${count} need you\` : "Nothing needs you"}`],
    ["      <SurfaceSection label=\"NEEDS YOU\" actions={reviewAction}>\n        <p className=\"room-empty-line\" data-testid=\"needs-you-empty\">\n          Nothing needs you{",
      `      <SurfaceSection label={${G}.__p13 ? "OPEN HERE" : "NEEDS YOU"} actions={reviewAction}>\n        <p className="room-empty-line" data-testid="needs-you-empty">\n          {${G}.__p13 ? "Nothing open" : "Nothing needs you"}{`],
    ["    <SurfaceSection label={`NEEDS YOU ${count}`} actions={reviewAction}>",
      `    <SurfaceSection label={${G}.__p13 ? \`OPEN HERE \${count}\` : \`NEEDS YOU \${count}\`} actions={reviewAction}>`],
  ]],
  // The scratch HOME reads as ~, exactly as the product already shows /Users/<name> (channels.ts).
  ["src/features/channels/channels.ts", null, [
    ["    case \"file\": return String(t.folder ?? \"\").replace(/^\\/Users\\/[^/]+/, \"~\");",
      "    case \"file\": return String(t.folder ?? \"\").replace(/^\\/Users\\/[^/]+/, \"~\").replace(/^\\/(private\\/)?tmp\\/p13c1-[^/]+/, \"~\");"],
  ]],
];

const met = new Set();
async function guard(server) {
  const miss = [];
  for (const [key] of SEATS) {
    const suffix = key.split("#")[0];
    if (!existsSync(`${web}${suffix}`)) { miss.push(`${key}: file not found`); continue; }
    try { await server.transformRequest(`/${suffix}`); } catch (e) { miss.push(`${key}: ${String(e.message || e).slice(0, 200)}`); continue; }
    if (!met.has(key)) miss.push(`${key}: transformed without its seats`);
  }
  if (miss.length) {
    console.error(`PHILO-13-11 SEAT GUARD: ${miss.length} seat(s) not met:\n  ${miss.join("\n  ")}`);
    process.exit(1);
  }
  console.log(`PHILO-13-11 SEAT GUARD: ${new Set(SEATS.map((x) => x[0].split("#")[0])).size} files, ${SEATS.length} seats, every anchor met`);
}

function seats() {
  return {
    name: "philo-13-11-seats",
    enforce: "pre",
    transform(code, id) {
      const file = id.split("?")[0];
      let out = null;
      for (const [key, imp, edits] of SEATS) {
        const suffix = key.split("#")[0];
        if (!file.endsWith(`/web/${suffix}`)) continue;
        met.add(key);
        out = out ?? code;
        for (const [anchor, repl, want = 1] of edits) {
          const n = typeof anchor === "string" ? out.split(anchor).length - 1 : (out.match(anchor) || []).length;
          if (n !== want) throw new Error(`PHILO-13-11 seat anchor in ${key}: found ${n}, want ${want}: ${String(anchor).slice(0, 90)}`);
          out = typeof anchor === "string" ? out.split(anchor).join(repl) : out.replace(anchor, repl);
        }
        if (imp) out = `${imp}\n${out}`;
      }
      return out;
    },
    configureServer(server) {
      server.httpServer?.once("listening", () => { void guard(server); });
    },
  };
}

export default {
  root: web,
  base: "/",
  configFile: false,
  plugins: [
    proposal && seats(),
    react(),
    {
      name: "philo-13-11-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "philo-13-11-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          (proposal
            ? `<script type="module" src="/@fs${harness}p13.tsx"></script>`
            : "") + `<script type="module" src="/@fs${harness}nav.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-philo-13-11" : "canvas-philo-13-11-today") },
  resolve: { alias: [{ find: "@w", replacement: `${web}src` }] },
  // Crawl every module at start: a dependency found late (a lazily opened window) makes vite
  // re-optimize and RELOAD the page mid-run (seen on glass: a blank board).
  optimizeDeps: { entries: ["index.html", "src/**/*.tsx", "src/**/*.ts", `${harness}p13.tsx`], holdUntilCrawlEnd: true },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4463),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
