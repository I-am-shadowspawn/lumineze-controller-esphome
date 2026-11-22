import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const script = fileURLToPath(new URL("../scripts/release-asset.sh", import.meta.url));

async function runRelease(mode, { draft = true, digest = "", uploadDigest } = {}) {
  const dir = await mkdtemp(join(tmpdir(), "dashboard-release-"));
  try {
    await mkdir(join(dir, "dist"));
    await mkdir(join(dir, "bin"));
    const contents = "dashboard asset\n";
    await writeFile(join(dir, "dist/lumineze-dashboard.js"), contents);
    const expected = `sha256:${createHash("sha256").update(contents).digest("hex")}`;
    await writeFile(join(dir, "digest"), digest === "expected" ? expected : digest);
    await writeFile(join(dir, "bin/gh"), `#!/bin/bash
set -eu
if [[ "$1 $2" == "release view" ]]; then
  if [[ "$*" == *"isDraft"* ]]; then echo "$DRAFT"; else cat "$STATE/digest"; fi
elif [[ "$1 $2" == "release upload" ]]; then
  printf '%s' "$UPLOAD_DIGEST" > "$STATE/digest"
  echo upload >> "$STATE/uploads"
else
  exit 1
fi
`, { mode: 0o755 });
    const result = spawnSync("bash", [script, mode], {
      cwd: dir,
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: `${join(dir, "bin")}:${process.env.PATH}`,
        RELEASE_TAG: "v-test",
        STATE: dir,
        DRAFT: String(draft),
        UPLOAD_DIGEST: uploadDigest === undefined ? expected : uploadDigest,
      },
    });
    const uploads = await readFile(join(dir, "uploads"), "utf8").catch(() => "");
    return { ...result, uploads };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

test("draft preparation uploads a missing asset and verifies its digest", async () => {
  const result = await runRelease("prepare");
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.uploads, "upload\n");
});

test("draft preparation is idempotent and never replaces an asset", async () => {
  const matching = await runRelease("prepare", { digest: "expected" });
  assert.equal(matching.status, 0, matching.stderr);
  assert.equal(matching.uploads, "");
  const mismatch = await runRelease("prepare", { digest: "sha256:wrong" });
  assert.notEqual(mismatch.status, 0);
  assert.match(mismatch.stderr, /digest mismatch/);
  assert.equal(mismatch.uploads, "");
});

test("preparation rejects published releases and checks uploaded digests", async () => {
  const published = await runRelease("prepare", { draft: false });
  assert.notEqual(published.status, 0);
  assert.match(published.stderr, /not a draft/);
  assert.equal(published.uploads, "");
  const badUpload = await runRelease("prepare", { uploadDigest: "sha256:wrong" });
  assert.notEqual(badUpload.status, 0);
  assert.match(badUpload.stderr, /digest mismatch/);
});

test("published verification requires a matching asset without uploading", async () => {
  for (const digest of ["", "sha256:wrong", "expected"]) {
    const result = await runRelease("verify", { draft: false, digest });
    assert.equal(result.status === 0, digest === "expected", result.stderr);
    assert.equal(result.uploads, "");
  }
});
