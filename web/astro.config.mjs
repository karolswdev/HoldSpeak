import { defineConfig } from "astro/config";

// HS-10-01: build into holdspeak/static/_built/ so the FastAPI runtime
// can serve the built output via a /_built mount, while the five legacy
// pages at holdspeak/static/*.html stay untouched. Each route rebuild
// (HS-10-06..09) will swap its FastAPI handler from reading the legacy
// file to reading from this build output, then delete the legacy file.

export default defineConfig({
  outDir: "../holdspeak/static/_built",
  base: "/_built",
  trailingSlash: "always",
  build: {
    format: "directory",
    assets: "_astro",
  },
  server: {
    host: "127.0.0.1",
    port: 4321,
  },
});
