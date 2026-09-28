// PHILO-9-03 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME.
//   CANVAS_MODE=proposal: ONE module swapped -- ProjectMemoryCore's
//     "../../features/project-room/ProjectRoomCore" resolves to the proposal
//     copy (which imports the proposed Update posture and controller) -- plus
//     shim.ts (the unbuilt wire, stated) and canvas.css, loaded before the app.
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
    proposal && {
      name: "philo-9-03-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          `<link rel="stylesheet" href="/@fs${harness}canvas.css"><script type="module" src="/@fs${harness}shim.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-philo-9-03" : "canvas-philo-9-03-today") },
  resolve: {
    alias: [
      ...(proposal
        ? [{ find: /^\.\.\/\.\.\/features\/project-room\/ProjectRoomCore$/, replacement: `${harness}ProposedProjectRoomCore.tsx` }]
        : []),
      { find: "@w", replacement: `${web}src` },
    ],
  },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4441),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
