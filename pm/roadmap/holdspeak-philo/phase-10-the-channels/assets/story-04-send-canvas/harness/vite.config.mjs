// PHILO-10-04 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME.
//   CANVAS_MODE=proposal: TWO modules swapped, nothing else --
//     ProjectRoomCore's "./update/UpdatePosture" -> harness/ProposedUpdatePosture.tsx
//       (the product's posture + the SEND well + the one history);
//     SettingsCore's "./connections" -> harness/ProposedConnections.tsx
//       (the product's Connections pane + the Destinations group under Tools);
//     plus shim.ts (the unbuilt wire, stated) and canvas.css, loaded before the app.
//   CANVAS_MODE=today: the product exactly as on this branch, no swap, no shim.
// HUB = the real hub's origin (shoot.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48801";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";

export default {
  root: web,
  base: "/",
  configFile: false,
  plugins: [
    react(),
    // Both modes: mount as the production bundle mounts (no StrictMode double
    // effects). Under StrictMode in dev, useResource's `mounted` ref is set
    // false by the first cleanup and never set true again
    // (web/src/pages/pageSupport.tsx:35-54), so Settings sits on "Loading"
    // forever in `vite dev`. A dev-only defect, named in the README; the
    // built bundle is unaffected.
    {
      name: "philo-10-04-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    proposal && {
      name: "philo-10-04-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          `<link rel="stylesheet" href="/@fs${harness}canvas.css"><script type="module" src="/@fs${harness}shim.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-philo-10-04" : "canvas-philo-10-04-today") },
  resolve: {
    alias: [
      ...(proposal
        ? [
            { find: /^\.\/update\/UpdatePosture$/, replacement: `${harness}ProposedUpdatePosture.tsx` },
            { find: /^\.\/connections$/, replacement: `${harness}ProposedConnections.tsx` },
          ]
        : []),
      { find: "@w", replacement: `${web}src` },
    ],
  },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4451),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
