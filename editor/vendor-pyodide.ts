// Copy Pyodide and the packages the browser-graded courses use into the output directory, so the
// site serves them itself: one origin to cache with the service worker, and no third-party request.
// The runtime comes from the npm package. The wheels come from the CDN of the same release and
// are checked against the sha256 the package's lock file holds.
import { createHash } from "node:crypto";
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

if (!process.argv[2])
  throw new Error("usage: node vendor-pyodide.ts OUTPUT_DIR");
const out = resolve(process.argv[2]);
const pkg = join(
  dirname(fileURLToPath(import.meta.url)),
  "node_modules",
  "pyodide",
);

// numpy, scipy and matplotlib are what Física computacional needs.
const WANTED = ["numpy", "scipy", "matplotlib"];
const RUNTIME = [
  "pyodide.mjs",
  "pyodide.asm.mjs",
  "pyodide.asm.wasm",
  "python_stdlib.zip",
];

interface Entry {
  file_name: string;
  sha256: string;
  depends: string[];
}
interface Lock {
  info: Record<string, string>;
  packages: Record<string, Entry>;
}

const { version } = JSON.parse(
  await readFile(join(pkg, "package.json"), "utf8"),
);
const lock: Lock = JSON.parse(
  await readFile(join(pkg, "pyodide-lock.json"), "utf8"),
);

const wanted = new Set<string>();
const add = (name: string) => {
  const entry = lock.packages[name];
  if (!entry) throw new Error(`pyodide ${version} has no package ${name}`);
  if (wanted.has(name)) return;
  wanted.add(name);
  entry.depends.forEach(add);
};
WANTED.forEach(add);

await mkdir(out, { recursive: true });
await Promise.all(RUNTIME.map((file) => cp(join(pkg, file), join(out, file))));
await writeFile(
  join(out, "pyodide-lock.json"),
  JSON.stringify({
    info: lock.info,
    packages: Object.fromEntries(
      [...wanted].map((name) => [name, lock.packages[name]]),
    ),
  }),
);

const sha256 = (data: Uint8Array) =>
  createHash("sha256").update(data).digest("hex");
async function wheel({ file_name, sha256: expected }: Entry) {
  const target = join(out, file_name);
  try {
    if (sha256(await readFile(target)) === expected) return;
  } catch {}
  const url = `https://cdn.jsdelivr.net/pyodide/v${version}/full/${file_name}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  const data = new Uint8Array(await response.arrayBuffer());
  if (sha256(data) !== expected)
    throw new Error(`${url}: the sha256 differs from the lock`);
  await writeFile(target, data);
}
await Promise.all([...wanted].map((name) => wheel(lock.packages[name])));
console.log(`pyodide ${version}: ${wanted.size} packages in ${out}`);
