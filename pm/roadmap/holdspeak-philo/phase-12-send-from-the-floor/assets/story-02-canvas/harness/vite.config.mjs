// PHILO-12-02 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME (the Phase 10/11 method,
// ../../../phase-11-more-documents-on-the-channels/assets/story-03-canvas/harness/).
//
//   CANVAS_MODE=proposal:
//     - SEATS: each product file the Floor send touches gets ONE named hook into
//       harness/p12.ts at a NAMED anchor (the SEATS table). A missing or doubled
//       anchor STOPS THE BUILD: the canvas never draws a seat the product file
//       does not have. Every hook is a `globalThis.__p12*` call that p12.ts
//       defines; with p12.ts absent each hook is a no-op and the product is
//       unchanged;
//     - ./ArtifactPullout resolves to harness/ProposedArtifactPullout.tsx (J1:
//       the SEND well, its three raw buttons as library Buttons);
//     - /desk/sprites/p12/* serves harness/sprites/ (the proposed art; nothing
//       lands in web/public);
//     - p12.ts (the unbuilt wire and the proposed composition, stated in its
//       header) and canvas.css, loaded before the app.
//   CANVAS_MODE=today: the product exactly as on this branch, no seat, no shim.
// HUB = the real hub's origin (shoot.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";
import { readFileSync, existsSync } from "node:fs";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48902";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";
const G = "(globalThis as any)";

/** [product file (suffix), import line or null, [[anchor, replacement, count?], ...]] */
const SEATS = [
  // The art: destination, brief and decision sprites resolve to the proposed files.
  ["src/desk/sprites.ts", null, [
    ["export function spriteName(kind: string, id: string): string {",
      `export function spriteName(kind: string, id: string): string {\n  const p12 = ${G}.__p12Sprite?.(kind, id); if (p12) return p12;`],
  ]],
  // F1, I1: the Floor layer -- destination icons and the brief icon join the scene AFTER the
  // object grid is laid out (the grid of real objects does not move), hit-tested as objects.
  ["src/desk/gl/sceneModel.ts", null, [
    // After the zones are laid out: the icons take cells that overlap no drawer and no object.
    ["  return {\n    objects,\n    zones,\n    dived: Boolean(input.divedZone),",
      `  objects.push(...((${G}.__p12FloorIcons?.(input, objects, zones)) ?? []));\n  return {\n    objects,\n    zones,\n    dived: Boolean(input.divedZone),`],
  ]],
  // G: the send rule in the drop matrix (per object, through the resolver); a refusal
  // tag does not light the target; release opens the dragged document's window.
  ["src/desk/gl/engine.ts", null, [
    ["        ? dropRule(target.kind, dragged.kind)\n        : null;",
      `        ? (${G}.__p12DropRule?.(target, dragged) ?? dropRule(target.kind, dragged.kind))\n        : null;`],
    ["      if (rule && target) {\n        const node = this.objects.get(target.key);",
      "      if (rule && target && rule.action !== \"p12-refused\") {\n        const node = this.objects.get(target.key);"],
    ["          } else if (dropped.action === \"file-knowledge\") {",
      `          } else if (dropped.action === "p12-send") {\n            ${G}.__p12Drop?.(obj, target, { x: e.clientX, y: e.clientY });\n          } else if (dropped.action === "p12-refused") {\n            // release does nothing (the tag said why)\n          } else if (dropped.action === "file-knowledge") {`],
    // F2/I2: opening a destination or the brief icon goes to its own place.
    [/state\.openPullout\(hit\.object\.id, \{ x: e\.clientX, y: e\.clientY \}\);/g,
      `if (!${G}.__p12OpenIcon?.(hit.object, { x: e.clientX, y: e.clientY })) state.openPullout(hit.object.id, { x: e.clientX, y: e.clientY });`, 2],
  ]],
  // G1, G4: the tag. Near the right edge (where every destination sits) it opens to the LEFT of
  // the cursor and never wraps; a refusal tag wears the warning look, not the accent of an act.
  ["src/desk/gl/WorldStage.tsx", null, [
    ["          className=\"desk-drop-verb\"\n          role=\"status\"",
      "          className=\"desk-drop-verb\"\n          data-refused={/^[A-Z][A-Z ]+$/.test(dropHint.verb) || undefined}\n          role=\"status\""],
    ["            left: dropHint.x + 14,",
      "            left: dropHint.x > window.innerWidth - 280 ? undefined : dropHint.x + 14,\n            right: dropHint.x > window.innerWidth - 280 ? window.innerWidth - dropHint.x + 14 : undefined,"],
  ]],
  // F2, I1: a destination or brief icon selected is not Ask context (Ask has nothing to read there):
  // the selection bar stays away while only those are selected.
  ["src/desk/components/AskPanel.tsx", null, [
    ["  if (!selectedIds.length || askOpen) return null;",
      "  if (!selectedIds.length || askOpen || selectedIds.every((r) => /^(destination:|intelligence:brief)/.test(r))) return null;"],
  ]],
  // H2 at 393 (Astra canvas r1 finding 2): the submenu's back row reads as a step back, not a
  // heading. Its mark is NOT in the glyph lane (glyph preferences hide that lane), it says Back,
  // and its accessible name is "Back".
  ["src/desk/components/DeskMenu.tsx", null, [
    ["            className=\"desk-menu-back\"\n            onClick={() => setOpenSub(null)}\n          >\n            {/* HS-148-01: the back row participates in the lane law. */}\n            <span className=\"desk-menu-glyph\" aria-hidden=\"true\">\n              {\"◂\"}\n            </span>\n            <span className=\"desk-menu-label\">{sub.label}</span>",
      "            className=\"desk-menu-back\"\n            aria-label=\"Back\"\n            data-p12=\"back\"\n            onClick={() => setOpenSub(null)}\n          >\n            <span className=\"desk-menu-backmark\" aria-hidden=\"true\">{\"◂\"}</span>\n            <span className=\"desk-menu-label\">Back<small className=\"quiet\" aria-hidden=\"true\"> · {sub.label}</small></span>"],
  ]],
  // J1: the registry still imports ./ArtifactPullout (the resolveId swap below depends on it).
  ["src/desk/pullouts/registry.ts", null, [
    ["import { ArtifactPullout } from \"./ArtifactPullout\";", "import { ArtifactPullout } from \"./ArtifactPullout\";"],
  ]],
  // H1, H3, H4: the ONE shared composition of the object menu (spatial Floor and list).
  ["src/desk/floorMenu.ts", null, [
    ["  const ctx: VerbContext = { selectedRef: target.ref };\n  const verbs = menuVerbs(\"object\");",
      `  const p12 = ${G}.__p12ObjectMenu?.(target); if (p12) return p12;\n  const ctx: VerbContext = { selectedRef: target.ref };\n  const verbs = menuVerbs("object");`],
    ["    ...danger.map((v) => item(v, ctx)),\n  ];\n}",
      `    ...danger.map((v) => item(v, ctx)),\n  ].flatMap((e) => ${G}.__p12Insert?.(target.ref, e) ?? [e]);\n}`],
  ]],
  // H5: the menu bar's Object menu, and at compact width the Go menu (which carries Object's verbs).
  ["src/desk/components/DeskMenuBar.tsx", null, [
    ["        onSelect: () => v.run(ctx),\n      });\n    }\n  };",
      `        onSelect: () => v.run(ctx),\n      });\n    }\n    if (id === "object") ${G}.__p12BarSend?.(ctx.selectedRef, out);\n  };`],
  ]],
  // H2, H6: the list carries the brief row; a row open goes through the same open paths.
  ["src/desk/components/DeskListView.tsx", null, [
    ["        : allObjects(items).filter((object) => object.kind !== \"roadmap\")",
      `        : [...allObjects(items).filter((object) => object.kind !== "roadmap"), ...((${G}.__p12ListRows?.()) ?? [])]`],
    ["            else openPullout(qualifiedRef(row.object.kind, row.object.id));",
      `            else if (!${G}.__p12OpenIcon?.(row.object)) openPullout(qualifiedRef(row.object.kind, row.object.id));`],
  ]],
  // G2, G7: the push seam -- a pick pushed into the well, an open well reacts in place.
  ["src/desk/surface/send/SendWell.tsx", null, [
    ["const bump = () => { store.tick++; store.subs.forEach((f) => f()); };",
      `const bump = () => { store.tick++; store.subs.forEach((f) => f()); };\n${G}.__p12Pick = (ref: string, id: string | null) => { store.picked.set(ref, id); bump(); };\n${G}.__p12Picked = (ref: string) => store.picked.get(ref) ?? null;`],
  ]],
  // G8: Summary -> Digest -> Follow-up keeps the picked destination.
  ["src/meetings/MeetingSendWell.tsx", null, [
    ["onChange={(v) => { formPick.set(meetingId, v as Form); setKind(v as Form); }} />",
      `onChange={(v) => { ${G}.__p12FormMove?.(meetingId, kind, v); formPick.set(meetingId, v as Form); setKind(v as Form); }} />`],
  ]],
  // I2, I3: the brief's exact-id handoff (GET /api/brief/{id}, story 01).
  ["src/desk/pullouts/views/BriefView.tsx", null, [
    ["apiFetch<MondayBrief | null>(\"/api/brief/latest\")",
      `apiFetch<MondayBrief | null>(${G}.__p12BriefId ? \`/api/brief/\${${G}.__p12BriefId}\` : "/api/brief/latest")`],
  ]],
  // G6, G9: the Room link { projectId, updateId, destinationId }, also when the Room is already open.
  ["src/features/project-room/ProjectRoomCore.tsx", `import { fetchUpdates as __p12FetchUpdates } from "./update/api";`, [
    ["  const updateCtrl = useUpdateController(\n    ctrl.projectId, () => void ctrl.load(),\n  );\n",
      `  const updateCtrl = useUpdateController(\n    ctrl.projectId, () => void ctrl.load(),\n  );\n  useEffect(() => {\n    const on = (e: Event) => {\n      const d = (e as CustomEvent).detail;\n      if (!d || d.projectId !== ctrl.projectId) return;\n      ${G}.__p12RoomLinkTaken = d.token;\n      void __p12FetchUpdates(d.projectId).then((list) => {\n        const u = list.find((x) => x.id === d.updateId);\n        if (!u) return;\n        updateCtrl.openUpdate(u);\n        ${G}.__p12Pick?.(\`project_update:\${u.id}\`, d.destinationId);\n        if (d.destinationId) ${G}.__p12Arrive?.(\`project_update:\${u.id}\`);\n      });\n    };\n    window.addEventListener("p12:room-link", on);\n    return () => window.removeEventListener("p12:room-link", on);\n  }, [ctrl.projectId, updateCtrl.openUpdate]);\n`],
  ]],
  // F2: Open on a destination icon lands on THAT destination's row in Settings (story 04).
  ["src/pages/cores/connections/Destinations.tsx", null, [
    ["  // B2, the arrival: once the group has drawn, bring it into view with the add form open.",
      `  useEffect(() => {\n    const on = (e: Event) => {\n      const d = (e as CustomEvent).detail;\n      setAdding(false); setEditing(null); setOpen(d.id);\n      window.setTimeout(() => [...document.querySelectorAll("[data-testid=dest-row]")]\n        .find((r) => r.querySelector(\`[data-destination="\${d.name}"]\`))?.scrollIntoView({ block: "center" }), 250);\n    };\n    window.addEventListener("p12:dest-row", on);\n    const pend = ${G}.__p12DestRow; if (pend) { ${G}.__p12DestRow = null; window.setTimeout(() => on(new CustomEvent("x", { detail: pend })), 0); }\n    return () => window.removeEventListener("p12:dest-row", on);\n  }, []);\n  // B2, the arrival: once the group has drawn, bring it into view with the add form open.`],
  ]],
];

// The guard's own proof: P12_GUARD_PROBE=<a product path that does not exist> adds one seat the
// guard must refuse (README, "The anchor guard"). Never set in a canvas run.
if (process.env.P12_GUARD_PROBE) SEATS.push([process.env.P12_GUARD_PROBE, null, [["__never__", ""]]]);

/** The guard (Astra canvas r1 finding 5): a seat file that is renamed, moved or deleted never
 *  reaches transform() -- so the server checks EVERY seat at start: the file exists and its
 *  transform meets every anchor. Any miss stops the server (exit 1) before a board is drawn. */
const met = new Set();
async function guard(server) {
  const miss = [];
  for (const [suffix] of SEATS) {
    if (!existsSync(`${web}${suffix}`)) { miss.push(`${suffix}: file not found`); continue; }
    try { await server.transformRequest(`/${suffix}`); } catch (e) { miss.push(`${suffix}: ${String(e.message || e).slice(0, 160)}`); continue; }
    if (!met.has(suffix)) miss.push(`${suffix}: transformed without its seats`);
  }
  if (miss.length) {
    console.error(`PHILO-12-02 SEAT GUARD: ${miss.length} seat(s) not met:\n  ${miss.join("\n  ")}`);
    process.exit(1);
  }
  console.log(`PHILO-12-02 SEAT GUARD: ${SEATS.length} files, every anchor met`);
}

function seats() {
  return {
    name: "philo-12-02-seats",
    enforce: "pre",
    transform(code, id) {
      const file = id.split("?")[0];
      for (const [suffix, imp, edits] of SEATS) {
        if (!file.endsWith(`/web/${suffix}`)) continue;
        met.add(suffix);
        let out = code;
        for (const [anchor, repl, want = 1] of edits) {
          const n = typeof anchor === "string" ? out.split(anchor).length - 1 : (out.match(anchor) || []).length;
          if (n !== want) throw new Error(`PHILO-12-02 seat anchor in ${suffix}: found ${n}, want ${want}: ${String(anchor).slice(0, 90)}`);
          out = typeof anchor === "string" ? out.split(anchor).join(repl) : out.replace(anchor, repl);
        }
        return imp ? `${imp}\n${out}` : out;
      }
      return null;
    },
    async resolveId(source, importer) {
      if (importer && source === "./ArtifactPullout" && importer.endsWith("/desk/pullouts/registry.ts"))
        return `${harness}ProposedArtifactPullout.tsx`;
      return null;
    },
    configureServer(server) {
      server.httpServer?.once("listening", () => { void guard(server); });
      // The proposed art, served beside the product's sprites (nothing written to web/public).
      server.middlewares.use("/desk/sprites/p12", (req, res, next) => {
        const f = `${harness}sprites${(req.url || "").split("?")[0]}`;
        if (!existsSync(f)) return next();
        res.setHeader("content-type", "image/png");
        res.end(readFileSync(f));
      });
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
    // Mount as the production bundle mounts (no StrictMode double effects).
    {
      name: "philo-12-02-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "philo-12-02-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          (proposal
            ? `<link rel="stylesheet" href="/@fs${harness}canvas.css"><script type="module" src="/@fs${harness}p12.ts"></script>`
            : "") + `<script type="module" src="/@fs${harness}nav.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-philo-12-02" : "canvas-philo-12-02-today") },
  resolve: { alias: [{ find: "@w", replacement: `${web}src` }] },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4462),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
