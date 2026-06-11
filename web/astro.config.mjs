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
  vite: {
    plugins: [
      {
        // Ship the page behavior un-minified. The bundle is served from a
        // loopback FastAPI mount (size is irrelevant), the pre-module
        // loader shipped the full un-minified source anyway (as a ?raw
        // string), readable JS is on-brand for a local-first tool, and
        // the integration tests assert real source markers in the served
        // chunks. Astro hardcodes `minify: true` for the client
        // environment (core/build/static-build.js), so a plain
        // `vite.build.minify: false` is ignored; this environment hook
        // is the supported override point.
        name: "holdspeak-unminified-client",
        configEnvironment(name) {
          if (name === "client") {
            return { build: { minify: false } };
          }
        },
      },
    ],
  },
});
