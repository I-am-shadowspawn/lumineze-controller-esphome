# T16 — Publish an immutable verified modular release

**Entry/dependencies:** T15 accepted hardware/upgrade report, T12 required checks,
T13 identity and T14 consumer instructions. **Delivery:** traceable stable source
and a working pinned consumer. Existing candidate tags are not this gate.

## Incremental deliveries

- [ ] **T16.1 — Freeze release scope and candidate.** Select the version under
  T13 policy, exact source SHA, supported profiles/hardware/toolchain and required
  evidence. Prefer all four profiles for Gate B. A seasonal-only release needs
  an explicit scope decision and must list schedule/T10–T12 acceptance as deferred,
  not passed. If T23 physical acceptance is still pending, withhold its stable
  support claim or defer promotion; do not label unvalidated controls verified.
  Acceptance: release manifest maps each capability to software and physical
  evidence, with no moving refs or unresolved release-blocking defects.
- [ ] **T16.2 — Reproducibility and consumer candidate gate.** Run required CI
  on the exact final candidate and clean remote consumers pinned to it. Align
  metadata, changelog, examples, migration and recovery instructions. If those
  edits change the source, run gates on the new final SHA. Acceptance: all
  advertised profiles build and inventories/sizes match the candidate; hardware
  results are applicable to it or affected tests are rerun.
- [ ] **T16.3 — Release package and approval-ready record.** Prepare release
  notes, manifest, checks, supported configurations, migration steps and known
  limits. Publish source and sanitized configuration artifacts as appropriate.
  Do not publish device-specific credential-bearing firmware; generic bootstrap
  binaries are T19/T21 scope. Acceptance: a reviewer can reproduce and correlate
  every artifact with source, toolchain and support evidence. Publication requires
  the actual release task's authorization after this concrete record exists.
- [ ] **T16.4 — Stable tag and remote verification.** Create the authorized
  immutable stable tag at the verified SHA, verify remote tag resolution and
  build the supported consumer examples through it. Publish the prepared notes
  once final tag checks pass. Acceptance: the tag and release version agree;
  dependencies use the same tag; no stable tag is force-moved. A failure after
  tagging is disclosed and corrected in a new version, not hidden by rewriting.
- [ ] **T16.5 — Deployment handoff.** Record final URLs, tag/SHA, checks and
  recovery instructions; update support status/examples and hand off the T17
  device checklist. Acceptance: users understand that source publication does
  not update a running controller; builds/installations are deliberate actions.

## Completion and rollback

A published tag without consumer/hardware evidence is incomplete. Retain previous
release/recovery tags. Withdraw recommendation of a defective release, document
its limits and issue a corrected version. Firmware rollback follows T15's storage
and calibration procedure, not a tag rewrite.

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
