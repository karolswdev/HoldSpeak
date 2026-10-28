// Keep the last three builds' assets (owner 2026-10-28: "It doesn't even load
// for me"). The web build no longer empties holdspeak/static/_built, so a desk
// tab opened before a rebuild can still fetch the chunks of its own build.
//
// Each build records the asset files it emitted, newest first, in
// `<outDir>/.builds.json`; every file in `<outDir>/assets` that no kept build
// names is removed. `web/vite.config.ts` calls `recordBuild` after it writes
// the bundle. A plain `node web/scripts/prune-builds.mjs <outDir>` prunes to
// the manifest as it stands.
import { existsSync, readdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const KEEP_BUILDS = 3;
export const MANIFEST = ".builds.json";

/** The kept builds, newest first ([] when there is no manifest). */
export function readBuilds(outDir) {
  try {
    const value = JSON.parse(readFileSync(join(outDir, MANIFEST), "utf8"));
    return Array.isArray(value) ? value.filter((build) => build && Array.isArray(build.assets)) : [];
  } catch {
    return [];
  }
}

/** The asset files the built index.html names (`/_built/assets/<file>`). */
export function indexAssets(outDir) {
  try {
    const html = readFileSync(join(outDir, "index.html"), "utf8");
    return [...html.matchAll(/assets\/([^"'?#\s)]+)/g)].map((match) => match[1]);
  } catch {
    return [];
  }
}

/** Remove every file in `<outDir>/assets` that no kept build names. */
export function pruneAssets(outDir, builds = readBuilds(outDir)) {
  const keep = new Set([...builds.flatMap((build) => build.assets), ...indexAssets(outDir)]);
  const dir = join(outDir, "assets");
  const removed = [];
  if (!existsSync(dir)) return removed;
  for (const name of readdirSync(dir)) {
    if (keep.has(name)) continue;
    const full = join(dir, name);
    if (!statSync(full).isFile()) continue;
    unlinkSync(full);
    removed.push(name);
  }
  return removed.sort();
}

/** Record this build's asset files, keep the newest `keep` builds, prune. */
export function recordBuild(outDir, assets, { buildId = "", keep = KEEP_BUILDS, now = new Date() } = {}) {
  const current = { build_id: buildId, built_at: now.toISOString(), assets: [...new Set(assets)].sort() };
  const same = (build) => build.assets.length === current.assets.length && build.assets.every((name, i) => name === current.assets[i]);
  // An unchanged rebuild replaces its own entry: it is the same build.
  const builds = [current, ...readBuilds(outDir).filter((build) => !same(build))].slice(0, keep);
  writeFileSync(join(outDir, MANIFEST), `${JSON.stringify(builds, null, 2)}\n`);
  const removed = pruneAssets(outDir, builds);
  return { builds, removed };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const outDir = process.argv[2] ?? fileURLToPath(new URL("../../holdspeak/static/_built/", import.meta.url));
  const removed = pruneAssets(outDir);
  console.log(`pruned ${removed.length} asset file(s) from ${outDir}`);
}
