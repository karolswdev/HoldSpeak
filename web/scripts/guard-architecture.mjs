import { readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const source = join(root, "src");
const files = [];
const walk = (directory) => {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) walk(path);
    else files.push(path);
  }
};
walk(source);

const failures = [];
const packageJson = JSON.parse(
  readFileSync(join(root, "package.json"), "utf8"),
);
for (const dependency of ["astro", "@astrojs/react", "alpinejs"]) {
  if (
    packageJson.dependencies?.[dependency] ||
    packageJson.devDependencies?.[dependency]
  )
    failures.push(`forbidden dependency: ${dependency}`);
}
for (const file of files) {
  const name = relative(root, file);
  if (extname(file) === ".astro") failures.push(`Astro source: ${name}`);
  if (
    ![".ts", ".tsx", ".css", ".d.ts"].some((extension) =>
      file.endsWith(extension),
    )
  )
    continue;
  const text = readFileSync(file, "utf8");
  if (/\bAlpine\b|x-(?:data|init|show|text)|client:(?:only|load)/i.test(text))
    failures.push(`legacy directive/runtime marker: ${name}`);
  if (/\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML\s*\(/.test(text))
    failures.push(`runtime HTML injection: ${name}`);
  if (/document\.(?:querySelector|querySelectorAll)\s*\(/.test(text))
    failures.push(`global selector bootstrap: ${name}`);
  if (/\bfetch\s*\(/.test(text) && name !== "src/lib/api.ts")
    failures.push(`request bypasses typed API client: ${name}`);
}

if (failures.length) {
  console.error(
    `React architecture guard failed:\n${failures.map((failure) => `- ${failure}`).join("\n")}`,
  );
  process.exit(1);
}
console.log(
  `React architecture guard passed (${files.length} source files; zero framework residue).`,
);
