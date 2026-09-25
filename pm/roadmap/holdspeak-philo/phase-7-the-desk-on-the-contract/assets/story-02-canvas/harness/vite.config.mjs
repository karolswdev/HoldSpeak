import { fileURLToPath, URL } from "node:url";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web", import.meta.url));

export default {
  root: harness,
  base: "/",
  publicDir: `${web}/public`,
  esbuild: { jsx: "automatic" },
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("canvas") },
  resolve: {
    alias: {
      "@w": `${web}/src`,
      react: `${web}/node_modules/react`,
      "react-dom": `${web}/node_modules/react-dom`,
    },
    dedupe: ["react", "react-dom"],
  },
  server: {
    host: "127.0.0.1",
    port: 4432,
    strictPort: true,
    fs: { allow: [web, harness] },
  },
};
