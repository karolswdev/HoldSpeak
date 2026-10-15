import { fileURLToPath, URL } from "node:url";
const canvas = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../web/", import.meta.url));
export default {
  root: canvas,
  base: "/",
  cacheDir: fileURLToPath(new URL("../../../../.tmp/settings-trials/canvas-vite", import.meta.url)),
  publicDir: `${web}public`,
  esbuild: { jsx: "automatic" },
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("settings-trial-direction") },
  resolve: { alias: { "@w": `${web}src`, react: `${web}node_modules/react`, "react-dom": `${web}node_modules/react-dom` }, dedupe: ["react", "react-dom"] },
  server: { host: "127.0.0.1", port: 4477, strictPort: true, fs: { allow: [web, canvas] } },
};
