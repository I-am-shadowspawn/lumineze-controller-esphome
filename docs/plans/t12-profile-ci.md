# T12 — Enforce the supported profile matrix

**Entry/dependencies:** T11 software acceptance. Design CI changes now; enable
schedule gates only when actual schedule fixtures exist. **Delivery:** required
checks that identify a failing profile and provide reproducible evidence.

## Required coverage

The four profiles are generic seasonal/schedule × production/development.
Legacy `ci/controller*.yaml` fixtures remain compatibility regressions, not two
additional engine capabilities. Keep the existing schema/topology matrix and
T23 tests. The current workflow skips documentation-only full validation and retries
compilation; preserve those outcomes. Hardware reports remain separate gates.

## Incremental deliveries

- [x] **T12.1 — Explicit coverage manifest.** Record profile, fixture, provider,
  engine, temporary capability, expected entities/state, toolchain and checks in
  a machine-readable manifest. Include repeated products, swapped/sparse slots,
  shared/independent groups, up to four experimental fixtures and negative
  configurations. Acceptance: each supported profile has a full-build job and
  each topology case declares config-only, compiled or hardware-verified status.
- [ ] **T12.2 — Deterministic fast gates.** Run schema failures, T10 vectors,
  actual policy transitions, transport/generation/T23 tests, seasonal parity,
  safe-off and timeout checks against the checkout. Acceptance: expected-invalid
  cases fail for the intended reason; a deliberately broken schedule case and
  stale-generation case each fail their named check. Remove injected faults
  before commit. No network package reference may hide a checkout change.
- [ ] **T12.3 — Isolated profile builds and inventories.** Compile all four
  profiles on `requirements-ci.txt`'s pin with distinct job/build directories.
  Assert exactly one provider/orchestrator/engine and one common output path.
  Compare production/development inventories; reject production test state and
  cross-engine private settings/state. Acceptance: remove one profile entry or
  inject an unwanted seasonal symbol in schedule and demonstrate detection;
  compiled-source evidence proves omission rather than hidden HA entities.
- [ ] **T12.4 — Resilience, size and artifacts.** Retain bounded retry/backoff
  for transient external downloads, cache by toolchain/profile/source inputs,
  and retain per-attempt logs without masking the final error. Record flash/RAM
  static sizes and warnings, with explicit reviewed budgets (aligned with T15).
  Scan retained configuration/logs/artifacts for fixture credentials; use only
  dummy secrets. Acceptance: final failed compilation fails CI; threshold breach
  fails its profile; artifacts cannot contain live credentials. Runtime heap
  headroom is not claimed from linker output.
- [ ] **T12.5 — Remote consumption and release gate.** Add a distinct clean
  consumer check against an immutable candidate SHA with package and component
  on that same SHA. Run all profiles remotely at release time; use a representative
  consumer on implementation PRs. Document required check names for repository
  branch protection; apply repository settings only when authorized.
  Acceptance: wrong/missing helper ref is detected and final candidate checks
  can be traced to the exact SHA. Documentation-only commits must not run full
  validation/builds. If required checks would stay pending under path-ignore,
  use a lightweight always-triggered path decision that reports success for
  docs-only changes and dispatches the full matrix for code changes. Verify both
  paths before enabling branch protection; do not strand documentation PRs.

## Completion and rollback

Record logs/check URLs, manifest and failure-injection evidence. Keep physical
support limits separate from compiled experimental topology. Roll back workflow
changes independently if infrastructure makes checks unusable; never weaken
behavioral acceptance or promote a profile without its build evidence.

## Execution and evidence rules

Use the [delivery index](t10-t17-delivery-index.md) for gate definitions and the
baseline. The checkboxes below are the canonical incremental tracker for this
task. Complete each increment in a separate reviewable commit after its checks
pass. Record source SHA, files, commands/results, evidence links, deviations and
remaining work beside that increment. Proposed filenames may change; ownership
and acceptance criteria may not silently change. Do not mark implementation or
hardware increments complete because this plan exists.

**Progress:** all increments planned; no implementation or hardware evidence
is claimed by this document.


### T12.1 — complete

Source `b3bc3bd`. `ci/profile-matrix.json` declares all four full-build profiles,
providers/capabilities/build directories, pin, dummy compatibility fixtures,
negative/fast checks and ten topology cases with separate software/physical
status. Dedicated `Profile / <profile>` jobs use the manifest fixture. The
manifest checker rejects missing entries, mismatched workflow matrix, pin or
capabilities. Static budgets are 180,000 RAM / 1,600,000 flash bytes, chosen above
all four T11 baselines while retaining 141,296 static RAM / 235,008 flash bytes
against the current partition; these do not certify runtime heap. Topology matrix
full compile remains required CI coverage, not a claim of physical validation.
Local manifest check passes. Next: deterministic gates and fault injection.
