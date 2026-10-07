// PHILO-14 canvas harness (copied from docs/internal/conductor-canvas/harness): the PRODUCT app as it is on main, served by vite against a REAL hub on
// an isolated HOME. The method is the story-15 canvas's
// (pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/harness/vite.config.mjs).
//
//   CANVAS_MODE=proposal: seats.mjs puts ONE named hook into a product file at a NAMED anchor.
//     A missing or doubled anchor STOPS THE SERVER (the seat guard). The hooks call the shim
//     (p14.tsx), which draws the proposal with library species only and names every
//     stand-in in its header.
//   CANVAS_MODE=today: the product exactly as on this branch, no seat, no shim.
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import P14 from "./seats.mjs";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48902";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";
const SHIM = `${harness}p14.tsx`;
const SEATS = proposal ? P14.map((x) => [`p:${x[0]}`, ...x.slice(1)]) : [];

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
    console.error(`P14 CANVAS SEAT GUARD: ${miss.length} seat(s) not met:\n  ${miss.join("\n  ")}`);
    process.exit(1);
  }
  console.log(`P14 CANVAS SEAT GUARD (p14): ${new Set(SEATS.map((x) => x[0].split(":")[1].split("#")[0])).size} files, ${SEATS.length} seats, every anchor met`);
}

function seats() {
  return {
    name: "p14-canvas-seats",
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
          if (n !== want) throw new Error(`p14 seat anchor in ${key}: found ${n}, want ${want}: ${String(anchor).slice(0, 90)}`);
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
      name: "p14-canvas-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "p14-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          (proposal ? `<script type="module" src="/@fs${SHIM}"></script>` : "")
            + `<script type="module" src="/@fs${harness}nav.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-p14" : "canvas-p14-today") },
  resolve: { alias: [{ find: "@w", replacement: `${web}src` }] },
  // Crawl every module at start: a dependency found late makes vite re-optimize and RELOAD.
  optimizeDeps: { entries: ["index.html", "src/**/*.tsx", "src/**/*.ts", ...(proposal ? [SHIM] : [])], holdUntilCrawlEnd: true },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4471),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
