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
- [x] **T12.2 — Deterministic fast gates.** Run schema failures, T10 vectors,
  actual policy transitions, transport/generation/T23 tests, seasonal parity,
  safe-off and timeout checks against the checkout. Acceptance: expected-invalid
  cases fail for the intended reason; a deliberately broken schedule case and
  stale-generation case each fail their named check. Remove injected faults
  before commit. No network package reference may hide a checkout change.
- [x] **T12.3 — Isolated profile builds and inventories.** Compile all four
  profiles on `requirements-ci.txt`'s pin with distinct job/build directories.
  Assert exactly one provider/orchestrator/engine and one common output path.
  Compare production/development inventories; reject production test state and
  cross-engine private settings/state. Acceptance: remove one profile entry or
  inject an unwanted seasonal symbol in schedule and demonstrate detection;
  compiled-source evidence proves omission rather than hidden HA entities.
- [x] **T12.4 — Resilience, size and artifacts.** Retain bounded retry/backoff
  for transient external downloads, cache by toolchain/profile/source inputs,
  and retain per-attempt logs without masking the final error. Record flash/RAM
  static sizes and warnings, with explicit reviewed budgets (aligned with T15).
  Scan retained configuration/logs/artifacts for fixture credentials; use only
  dummy secrets. Acceptance: final failed compilation fails CI; threshold breach
  fails its profile; artifacts cannot contain live credentials. Runtime heap
  headroom is not claimed from linker output.
- [x] **T12.5 — Remote consumption and release gate.** Add a distinct clean
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

**Progress:** all software increments complete. Current GitHub execution remains a review gate; hardware/release gates remain open.


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


### T12.2 — complete

`check_fast_gates.py` runs the manifest-declared checkout-only harnesses and fixture
C++ tests with named failures. It requires executable PASS coverage for every
T10 transition ID. Nine real schedule schema cases and both engine topology
matrices are added to CI alongside existing failures and inventory checks.
`check_gate_faults.py` copies only source/test assets into a disposable directory
and proves a changed oracle expectation fails `check_schedule_cases` and an
obsolete completion that clears pending state fails `check_schedule_policy`.
Both failed by assertions, not setup/compile errors; no injected fault touched
the checkout. All unmodified fast gates pass (`/tmp/t12-fast.log`), as do the nine
schedule and 17 existing schema cases. Next: isolated build inventory gates.


### T12.3 — complete

Each profile has its own matrix job/checkout/build directory with fail-fast off.
Generated-source gates require the selected provider/engine/common policy and
forbid the alternative provider, engine-private state and unsupported capability
entities. Production test symbols are absent. All four current-source checks pass.
`check_build_gate_faults.py` proves deleting schedule-development is rejected by
manifest validation and injecting cross-engine state into each real generated
source is rejected by its named isolation check. CI runs these checks after each
profile build. T11 records local pinned full builds; the complete experimental
matrix is additionally running and will be recorded under T12.4. No hardware
or HA runtime outcome is inferred from these checks.


### T12.4 — in progress

- [x] **T12.4a — Bounded retries, budgets and artifact boundary.** The shared
  `build_profile.py` retains each attempt and propagates the final failure,
  validates dummy inputs before logging, checks the reviewed RAM/flash budgets,
  and records exact source/toolchain/size/warnings without claiming hardware proof.
  Per-profile/source/toolchain cache keys and 14-day sanitized log/summary artifacts
  are configured. Artifact upload requires its boundary check to succeed.
  `check_build_resilience.py` proves three failures propagate exit 23, waits are
  20/40 seconds, all three logs remain, a RAM breach fails and private input fails
  before build logging. A real schedule-production run passes its budget and
  artifact scan (`/tmp/t12-build-artifacts`, `/tmp/t12-profile-build.log`).
- [x] **T12.4b — Complete topology matrix build record.** Both ten-case engine
  matrices are running locally; record their complete results before closing
  this increment. Static RAM does not certify free/minimum heap.


### T12.5 — complete

`check_remote_consumer.py` writes only an ordinary installation wrapper in an
empty temporary directory, pins packages/component to the same full SHA, rejects
wrong/missing helper refs, and validates/compiles without local assets or a
consumer generator requirement. Representative schedule production succeeds at
remote `78075b90d47e9b856efa11b3a6b7bbbfca37e499`
(`/tmp/t12-remote-consumer.log`); dispatch release rehearsals compile all four.
Remote compile also uses the bounded retry helper while retaining the empty
consumer working directory.
Always-triggered Change scope and Required validation replace path-ignore.
Disposable real Git event tests prove docs-only skip and firmware full-check
selection. The actual final gate script accepts documented skips/all-pass and
rejects a failed profile or scope job. `docs/ci-validation.md` names required
checks; repository branch protection is not changed. Both engine topology
compile matrices are required. T12.4b's local complete matrix record remains
pending before closing the parent task.


T12.4b complete: both ten-case topology matrices pass config and full compile on
ESPHome 2026.9.0, including swapped/sparse/repeated products, independent groups,
one/two contexts, four experimental fixtures and development input. Declaration
reordering retains slot/calibration identities for both engines. Logs:
`/tmp/t12-seasonal-matrix-build.log`, `/tmp/t12-schedule-matrix-build.log`.
Manifest statuses now record actual compile evidence and retain physical pending.
New commits supersede previous same-ref workflow runs. All five T12 increments
are complete locally. GitHub's current candidate checks still need review after
runner scheduling; completed/cancelled obsolete runs are not acceptance evidence.
Next: T13 identity/compatibility decisions; no hardware promotion.
