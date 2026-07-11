import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "/_built/",
  plugins: [react()],
  build: {
    outDir: "../holdspeak/static/_built",
    emptyOutDir: true,
    assetsDir: "assets",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          desk: ["./src/desk/DeskApp.tsx"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: { host: "127.0.0.1", port: 4321 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    css: true,
  },
});
