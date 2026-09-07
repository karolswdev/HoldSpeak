import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * HS-200-02 (contract C1): the build id this bundle was made from.
 *
 * A digest of every web source file plus the package manifest and this config.
 * Deterministic, so an unchanged rebuild keeps its id and never reads as a
 * stale bundle; any change to the shipped source produces a new one.
 *
 * It reaches two places, on purpose:
 *  - `__HOLDSPEAK_BUILD__`, compiled into the bundle, so the LOADED page
 *    identifies its own build without asking the backend.
 *  - `build-id.json` beside the emitted assets, which the SERVER reads once at
 *    process start. That capture is what a later Git checkout cannot change.
 */
const here = fileURLToPath(new URL(".", import.meta.url));

function sourceFiles(dir: string, found: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) =>
    a.name < b.name ? -1 : 1,
  )) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) sourceFiles(full, found);
    else if (/\.(tsx?|jsx?|css|json|html|svg)$/.test(entry.name)) found.push(full);
  }
  return found;
}

function computeBuildId(): string {
  const digest = createHash("sha256");
  const roots = [join(here, "src"), join(here, "public")];
  for (const root of roots) {
    let files: string[] = [];
    try {
      files = sourceFiles(root);
    } catch {
      continue;
    }
    for (const file of files) {
      digest.update(file.slice(here.length));
      digest.update(readFileSync(file));
    }
  }
  for (const manifest of ["package.json", "index.html", "vite.config.ts"]) {
    try {
      digest.update(readFileSync(join(here, manifest)));
    } catch {
      // Absent in this checkout: the remaining inputs still identify the build.
    }
  }
  return digest.digest("hex").slice(0, 16);
}

const BUILD_ID = computeBuildId();

/** Write the id where the server and a curious human can both find it. */
function buildStamp() {
  return {
    name: "holdspeak-build-stamp",
    writeBundle(options: { dir?: string }) {
      const dir = options.dir;
      if (!dir) return;
      writeFileSync(
        join(dir, "build-id.json"),
        `${JSON.stringify({ build_id: BUILD_ID, built_at: new Date().toISOString() }, null, 2)}\n`,
      );
      const indexPath = join(dir, "index.html");
      try {
        const html = readFileSync(indexPath, "utf8");
        const meta = `<meta name="holdspeak-build" content="${BUILD_ID}">`;
        const stamped = /<meta name="holdspeak-build"[^>]*>/.test(html)
          ? html.replace(/<meta name="holdspeak-build"[^>]*>/, meta)
          : html.replace("</head>", `    ${meta}\n  </head>`);
        writeFileSync(indexPath, stamped);
      } catch {
        // No index.html in this output: the JSON stamp stands alone.
      }
    },
  };
}

export default defineConfig({
  base: "/_built/",
  plugins: [react(), buildStamp()],
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(BUILD_ID) },
  build: {
    outDir: "../holdspeak/static/_built",
    emptyOutDir: true,
    assetsDir: "assets",
    sourcemap: process.env.HOLDSPEAK_WEB_SOURCEMAPS === "1",
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
    exclude: ["**/_parked/**", "**/node_modules/**"],
  },
});
