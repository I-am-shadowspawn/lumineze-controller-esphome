import { copyFile, mkdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = resolve(root, "dashboard-companion/src/lumineze-dashboard.js");
const output = resolve(root, "dist/lumineze-dashboard.js");
const text = await readFile(source, "utf8");
if (/^\s*import\s/m.test(text)) {
  throw new Error("The Marketplace asset must be self-contained");
}
await mkdir(dirname(output), { recursive: true });
await copyFile(source, output);
console.log(`Built ${output}`);
