// Title bar canvas (owner 2026-10-03: "the title bar looks terrible"): the PRODUCT app
// (web/index.html, web/src/main.tsx) exactly as on main, served by vite against a REAL hub
// on an isolated HOME. The C1 canvas method (../../story-11-canvas/harness/vite.config.mjs,
// CANVAS_MODE=today): no seat, no shim. The only addition is nav.ts (window.__p13Open: what a
// Dock click or a menu row does, called directly). The title bar proposals are CSS that
// shoot.py injects AFTER the app's CSS (proposals/*.css); the control injects nothing.
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48902";

export default {
  root: web,
  base: "/",
  configFile: false,
  plugins: [
    react(),
    {
      name: "titlebar-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "titlebar-canvas-nav",
      transformIndexHtml: (html) => html.replace("</head>", `<script type="module" src="/@fs${harness}nav.ts"></script></head>`),
    },
  ],
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("canvas-philo-13-titlebar") },
  resolve: { alias: [{ find: "@w", replacement: `${web}src` }] },
  optimizeDeps: { entries: ["index.html", "src/**/*.tsx", "src/**/*.ts"], holdUntilCrawlEnd: true },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4464),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
