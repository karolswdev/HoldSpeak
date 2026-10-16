import { fileURLToPath, URL } from "node:url";
import { realpathSync } from "node:fs";
const canvas = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../web/", import.meta.url));
export default {
  root: canvas, base: "/", publicDir: `${web}public`,
  cacheDir: fileURLToPath(new URL("../../../../.tmp/entry/canvas-presence-vite", import.meta.url)),
  esbuild: { jsx: "automatic" },
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("presence-direction") },
  resolve: { alias: { "@w": `${web}src`, react: `${web}node_modules/react`, "react-dom": `${web}node_modules/react-dom`, "react-router-dom": `${web}node_modules/react-router-dom` }, dedupe: ["react", "react-dom"] },
  server: { host: "127.0.0.1", port: 4499, strictPort: true, fs: { allow: [web, canvas, realpathSync(`${web}node_modules`)] } },
};
