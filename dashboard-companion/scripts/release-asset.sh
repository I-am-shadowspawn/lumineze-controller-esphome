#!/usr/bin/env bash
set -euo pipefail

asset="dist/lumineze-dashboard.js"
expected="sha256:$(sha256sum "$asset" | cut -d' ' -f1)"

if [[ "${1:-}" == "prepare" ]]; then
  draft="$(gh release view "$RELEASE_TAG" --json isDraft --jq '.isDraft')"
  if [[ "$draft" != "true" ]]; then
    echo "Release $RELEASE_TAG is not a draft; published releases cannot be prepared." >&2
    exit 1
  fi
elif [[ "${1:-}" != "verify" ]]; then
  echo "Usage: $0 prepare|verify" >&2
  exit 1
fi

actual="$(gh release view "$RELEASE_TAG" --json assets --jq '.assets[] | select(.name == "lumineze-dashboard.js") | .digest')"
if [[ -z "$actual" && "$1" == "prepare" ]]; then
  gh release upload "$RELEASE_TAG" "$asset"
  actual="$(gh release view "$RELEASE_TAG" --json assets --jq '.assets[] | select(.name == "lumineze-dashboard.js") | .digest')"
fi

if [[ "$actual" != "$expected" ]]; then
  echo "Dashboard asset missing or digest mismatch for $RELEASE_TAG (expected $expected, got ${actual:-<missing>})." >&2
  exit 1
fi
echo "Dashboard asset verified for $RELEASE_TAG: $actual"
