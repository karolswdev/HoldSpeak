import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

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
    else if (/\.(tsx?|jsx?|css|json|html|svg|png)$/.test(entry.name)) found.push(full);
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
  for (const manifest of ["package.json", "index.html", "briefing.html", "vite.config.ts"]) {
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
    async writeBundle(options: { dir?: string }, bundle: Record<string, unknown>) {
      const dir = options.dir;
      if (!dir) return;
      // 2026-10-28: keep the last three builds' assets, so a desk tab opened
      // before this build still loads its own chunks (scripts/prune-builds.mjs).
      const assets = Object.keys(bundle)
        .filter((name) => name.startsWith("assets/"))
        .map((name) => name.slice("assets/".length));
      // Loaded from the web root (the build's working directory), not beside
      // this file: a copy of this config elsewhere still finds the helper.
      const pruneBuilds = pathToFileURL(resolve(process.cwd(), "scripts", "prune-builds.mjs")).href;
      const { recordBuild } = await import(pruneBuilds);
      recordBuild(dir, assets, { buildId: BUILD_ID });
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

// html-to-image 1.11.13 reads a CSSFontFaceDeclaration as though it were
// CSSStyleDeclaration. Firefox requires the descriptor accessor instead.
// Keep the one-line upstream compatibility fix with the pinned dependency:
// https://github.com/bubkoo/html-to-image/issues/508
function feedbackFontDescriptors() {
  return {
    name: "holdspeak-feedback-font-descriptors",
    enforce: "pre" as const,
    transform(code: string, id: string) {
      if (!/\/html-to-image\/(?:es|lib)\/embed-webfonts\.js(?:\?|$)/.test(id)) return;
      return code.replaceAll("rule.style.fontFamily", "rule.style.getPropertyValue('font-family')");
    },
  };
}

const REACT_CHUNK = /\/node_modules\/(react|react-dom|react-router-dom|react-router|scheduler)\//;
const DESK_ROOT = resolve(here, "src/desk/DeskApp.tsx");
const BRIEFING_ROOT = resolve(here, "src/briefing/main.tsx");
const BRIEFING_DIR = resolve(here, "src/briefing") + "/";
type ModuleGraph = { getModuleInfo(id: string): { importedIds: readonly string[] } | null };
const reach = new Map<string, Set<string>>();

function reachable(root: string, graph: ModuleGraph): Set<string> {
  const known = reach.get(root);
  if (known) return known;
  const seen = new Set<string>();
  const queue = [root];
  while (queue.length) {
    const id = queue.pop() as string;
    if (seen.has(id)) continue;
    seen.add(id);
    for (const next of graph.getModuleInfo(id)?.importedIds ?? []) queue.push(next);
  }
  reach.set(root, seen);
  return seen;
}

function chunkFor(id: string, graph: ModuleGraph): string | undefined {
  if (REACT_CHUNK.test(id)) return "react";
  // Rollup's own helpers (\0commonjsHelpers …) follow their importers: a
  // helper the react chunk needs placed in "kit" made the two chunks import
  // each other, and React was undefined when the page ran.
  if (id.startsWith("\0")) return undefined;
  // Its own named chunk: a manual chunk pulls in the unassigned modules it
  // imports, so a shared module left unassigned would land in "desk".
  if (reachable(BRIEFING_ROOT, graph).has(id)) return id.startsWith(BRIEFING_DIR) ? undefined : "kit";
  if (reachable(DESK_ROOT, graph).has(id)) return "desk";
  return undefined;
}

/** PG-DIRECTION DIR2 (§8 "The page's script reads the desk's owner token"):
 *  the build fails when any chunk the briefing page loads holds the desk's
 *  auth client. */
function briefingKeepsNoAuth() {
  return {
    name: "holdspeak-briefing-keeps-no-auth",
    generateBundle(_options: unknown, bundle: Record<string, { type: string; name?: string; isEntry?: boolean; imports?: string[]; moduleIds?: string[] }>) {
      const entry = Object.entries(bundle).find(([, chunk]) => chunk.type === "chunk" && chunk.isEntry && chunk.name === "briefing");
      if (!entry) return;
      const queue = [entry[0]];
      const seen = new Set<string>();
      while (queue.length) {
        const name = queue.pop() as string;
        if (seen.has(name)) continue;
        seen.add(name);
        const chunk = bundle[name];
        if (!chunk || chunk.type !== "chunk") continue;
        const auth = (chunk.moduleIds ?? []).find((moduleId) => moduleId.endsWith("/src/lib/auth.ts"));
        if (auth) throw new Error(`the briefing page loads ${name}, which holds the desk's auth client (${auth})`);
        queue.push(...(chunk.imports ?? []));
      }
    },
  };
}

export default defineConfig({
  base: "/_built/",
  plugins: [react(), feedbackFontDescriptors(), buildStamp(), briefingKeepsNoAuth()],
  optimizeDeps: { exclude: ["html-to-image"] },
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(BUILD_ID) },
  build: {
    outDir: "../holdspeak/static/_built",
    // Never empty: an open desk tab still asks for the last builds' chunks.
    emptyOutDir: false,
    assetsDir: "assets",
    sourcemap: process.env.HOLDSPEAK_WEB_SOURCEMAPS === "1",
    rollupOptions: {
      // PG-DIRECTION DIR2 (2026-10-31): the briefing page is its own entry
      // (briefing.html → /_built/briefing.html, served at /b/<token>). It
      // shares the material and the kit, never the desk's auth client.
      input: { index: resolve(here, "index.html"), briefing: resolve(here, "briefing.html") },
      output: {
        // The desk chunk holds DeskApp's static graph, as before, LESS what
        // the briefing page imports: those modules form the "kit" chunk, so
        // the page never loads (or runs) the desk and its auth client.
        manualChunks: chunkFor,
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
