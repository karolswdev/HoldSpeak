import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { defineConfig } = require(resolve("web/node_modules/vite"));
const react = require(resolve("web/node_modules/@vitejs/plugin-react"));

const here = fileURLToPath(new URL(".", import.meta.url));
const repo = resolve(here, "../../../../");
const web = resolve(repo, "web");

export default defineConfig({
  root: here,
  plugins: [(react.default ?? react)({ jsxRuntime: "automatic" })],
  resolve: {
    alias: [
      { find: "@production", replacement: resolve(web, "src") },
      { find: "react-dom/client", replacement: resolve(web, "node_modules/react-dom/client.js") },
      { find: "react-dom", replacement: resolve(web, "node_modules/react-dom/index.js") },
      { find: "react/jsx-runtime", replacement: resolve(web, "node_modules/react/jsx-runtime.js") },
      { find: "react/jsx-dev-runtime", replacement: resolve(web, "node_modules/react/jsx-dev-runtime.js") },
      { find: "react", replacement: resolve(web, "node_modules/react/index.js") },
      { find: "motion/react", replacement: resolve(web, "node_modules/motion/dist/es/react.mjs") },
      { find: "@use-gesture/react", replacement: resolve(web, "node_modules/@use-gesture/react/dist/use-gesture-react.esm.js") },
      { find: "zustand/react", replacement: resolve(web, "node_modules/zustand/react.js") },
      { find: "zustand/vanilla", replacement: resolve(web, "node_modules/zustand/vanilla.js") },
      { find: "zustand", replacement: resolve(web, "node_modules/zustand/index.js") },
      { find: "@fontsource", replacement: resolve(web, "node_modules/@fontsource") },
    ],
  },
  publicDir: resolve(web, "public"),
  server: {
    host: "127.0.0.1",
    port: 4399,
    strictPort: true,
  },
  build: {
    outDir: resolve(here, "dist"),
    emptyOutDir: true,
  },
});
