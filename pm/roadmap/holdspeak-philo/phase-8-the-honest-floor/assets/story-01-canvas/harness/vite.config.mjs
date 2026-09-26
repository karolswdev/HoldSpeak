// PHILO-8-01 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME, with ONE module
// swapped: DeskApp's `./components/DeskListView` resolves to the proposal copy.
// HUB = the real hub's origin (shoot.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48801";

export default {
  root: web,
  base: "/",
  configFile: false,
  plugins: [
    react(),
    {
      name: "philo-8-01-canvas-css",
      transformIndexHtml: (html) =>
        html.replace("</head>", `<link rel="stylesheet" href="/@fs${harness}canvas.css"></head>`),
    },
  ],
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("canvas-philo-8-01") },
  resolve: {
    alias: [
      { find: /^\.\/components\/DeskListView$/, replacement: `${harness}ProposedDeskListView.tsx` },
      { find: "@w", replacement: `${web}src` },
    ],
  },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4433),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
