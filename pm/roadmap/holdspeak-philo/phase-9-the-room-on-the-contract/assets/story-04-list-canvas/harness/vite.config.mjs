// PHILO-9-04 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME. With PROPOSAL=1 three
// species are swapped for their marked PROPOSAL copies:
//   DeskApp's ./components/DeskListView     -> ProposedDeskListView.tsx
//   every ./DeskSortableTable               -> ProposedDeskSortableTable.tsx
//   every (../)components/DeskMenu, ./DeskMenu -> ProposedDeskMenu.tsx
// With PROPOSAL=0 nothing is swapped: board 0 is the product as it is today.
// HUB = the real hub's origin (shoot.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48801";
const proposal = process.env.PROPOSAL === "1";

const swaps = proposal
  ? [
      { find: /^\.\/components\/DeskListView$/, replacement: `${harness}ProposedDeskListView.tsx` },
      { find: /^\.\/DeskSortableTable$/, replacement: `${harness}ProposedDeskSortableTable.tsx` },
      { find: /^(?:\.\.?\/)+(?:components\/)?DeskMenu$/, replacement: `${harness}ProposedDeskMenu.tsx` },
    ]
  : [];

export default {
  root: web,
  base: "/",
  configFile: false,
  cacheDir: `${tmpdir()}/philo9-04-vite-${proposal ? "proposal" : "today"}`,
  plugins: [react()],
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(`canvas-philo-9-04-${proposal ? "proposal" : "today"}`) },
  resolve: {
    alias: [...swaps, { find: "@w", replacement: `${web}src` }],
  },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4443),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
