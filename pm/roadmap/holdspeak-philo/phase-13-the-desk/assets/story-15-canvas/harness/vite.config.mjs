// PHILO-13-15 (C5) and PHILO-13-17 (C7) canvas harness: the PRODUCT app as it is on
// main (web/index.html, web/src/main.tsx; the ratified C1 frame and Chair are BUILT
// there), served by vite against a REAL hub on an isolated HOME. The method is C1's
// (../../story-11-canvas/harness/vite.config.mjs).
//
//   CANVAS_MODE=proposal: each story's SEATS (seats-c5.mjs here, seats-c7.mjs in
//     ../../story-17-canvas/harness/) put ONE named hook into a product file at a
//     NAMED anchor. A missing or doubled anchor STOPS THE SERVER (the seat guard).
//     The hooks call the story's shim (c5.tsx / c7.tsx), which draws the proposal
//     with library species only and names every stand-in in its header.
//   CANVAS_SHIMS=c5 | c7 | c5,c7: which stories' seats and shims load.
//   CANVAS_MODE=today: the product exactly as on this branch, no seat, no shim.
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import C5 from "./seats-c5.mjs";
import C7 from "../../story-17-canvas/harness/seats-c7.mjs";
import COMMON from "./seats-common.mjs";

const harness = fileURLToPath(new URL(".", import.meta.url));
const h17 = fileURLToPath(new URL("../../story-17-canvas/harness/", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48902";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";
const shims = (process.env.CANVAS_SHIMS || "c5").split(",").filter(Boolean);
const SHIM = { c5: { seats: C5, file: `${harness}c5.tsx` }, c7: { seats: C7, file: `${h17}c7.tsx` } };
const SEATS = proposal ? [...COMMON.map((x) => [`common:${x[0]}`, ...x.slice(1)]), ...shims.flatMap((s) => SHIM[s].seats.map((x) => [`${s}:${x[0]}`, ...x.slice(1)]))] : [];

const met = new Set();
async function guard(server) {
  const miss = [];
  for (const [key] of SEATS) {
    const suffix = key.split(":")[1].split("#")[0];
    if (!existsSync(`${web}${suffix}`)) { miss.push(`${key}: file not found`); continue; }
    try { await server.transformRequest(`/${suffix}`); } catch (e) { miss.push(`${key}: ${String(e.message || e).slice(0, 200)}`); continue; }
    if (!met.has(key)) miss.push(`${key}: transformed without its seats`);
  }
  if (miss.length) {
    console.error(`PHILO-13-15/17 SEAT GUARD: ${miss.length} seat(s) not met:\n  ${miss.join("\n  ")}`);
    process.exit(1);
  }
  console.log(`PHILO-13-15/17 SEAT GUARD (${shims.join("+")}): ${new Set(SEATS.map((x) => x[0].split(":")[1].split("#")[0])).size} files, ${SEATS.length} seats, every anchor met`);
}

function seats() {
  return {
    name: "philo-13-c57-seats",
    enforce: "pre",
    transform(code, id) {
      const file = id.split("?")[0];
      let out = null;
      for (const [key, imp, edits] of SEATS) {
        const suffix = key.split(":")[1].split("#")[0];
        if (!file.endsWith(`/web/${suffix}`)) continue;
        met.add(key);
        out = out ?? code;
        for (const [anchor, repl, want = 1] of edits) {
          const n = out.split(anchor).length - 1;
          if (n !== want) throw new Error(`PHILO-13-15/17 seat anchor in ${key}: found ${n}, want ${want}: ${String(anchor).slice(0, 90)}`);
          out = out.split(anchor).join(repl);
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
      name: "philo-13-c57-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "philo-13-c57-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          (proposal ? shims.map((s) => `<script type="module" src="/@fs${SHIM[s].file}"></script>`).join("") : "")
            + `<script type="module" src="/@fs${harness}nav.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? `canvas-philo-13-${shims.join("-")}` : "canvas-philo-13-today") },
  resolve: { alias: [{ find: "@w", replacement: `${web}src` }] },
  // Crawl every module at start: a dependency found late makes vite re-optimize and RELOAD.
  optimizeDeps: { entries: ["index.html", "src/**/*.tsx", "src/**/*.ts", ...(proposal ? shims.map((s) => SHIM[s].file) : [])], holdUntilCrawlEnd: true },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4471),
    strictPort: true,
    fs: { allow: [web, harness, h17] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
