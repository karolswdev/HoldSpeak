import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The conductor serves the built assets from uat/web/dist at its own origin, so
// relative asset paths and same-origin /api calls both work. In dev, proxy /api
// to the conductor (default :8799) so `npm run dev` drives a real run.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    port: 5199,
    proxy: {
      "/api": { target: "http://127.0.0.1:8799", changeOrigin: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.js"],
  },
});
