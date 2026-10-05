# T17 — Existing-device migration and second-controller proof

**Entry/dependencies:** T16 verified release and T15 recovery procedure.
Preparation can proceed now; deployment waits for the release gate and explicit
physical deployment authorization. **Delivery:** actual upgrade and fresh-install
evidence for Gate B, without per-device implementation forks.

## Incremental deliveries

- [ ] **T17.1 — Prepare private device records and rollout.** Inventory the
  existing Skink controller's YAML/recovery release, actual physical assignments,
  maxima/seasonal settings, HA entities/automations and private access data.
  Establish release/profile, deployment window, safe lamp levels, observation
  period (at least an agreed operating cycle) and rollback triggers before work.
  Choose a bench second-controller setup if no second enclosure is available.
  Acceptance: private backup verified, serial recovery available, lamp identities
  checked physically, scope and authorization recorded. Public evidence redacts
  secrets and MACs.
- [ ] **T17.2 — Build existing-device wrapper and rehearse.** Convert installation
  data to the minimal pinned seasonal production example without copying engine
  logic. Map old settings explicitly; preserve compatible identity only where
  T15 proves it. Validate/compile and bench-rehearse its settings/HA migration.
  Acceptance: release refs match for package/helper, development is absent,
  settings reset/import steps and HA automation changes are reviewable before
  live installation. Never assume a legacy YAML ID migrates generic preferences.
- [ ] **T17.3 — Install and observe existing controller.** Install in the
  authorized window; verify default-off control state, per-lamp calibration,
  low/off readback, HA integration and safe commissioning before automatic enable.
  Observe the agreed cycle and applicable T23 cases only if release support is
  verified. Acceptance: target/request/completed/report evidence matches the
  release, settings and automations work, HA loss is autonomous, no rollback
  trigger occurs. Keep deployment and recovery logs.
- [ ] **T17.4 — Provision second ESP32-C3 from the example.** Create only new
  identity, credentials, MACs, topology and installation settings; build/install
  the same stable production release. Commission each fixture deliberately.
  Acceptance: no copied implementation sections, shared credentials, accidental
  lamp cross-targeting or hidden per-device patch. Both controllers are independently
  configurable and their physical assignments match their wrappers.
- [ ] **T17.5 — Resolve installation friction centrally.** Record every unclear
  step, configuration error and missing entity/migration instruction. Fix shared
  docs or implementation with reviewable commits and rerun relevant gates; code
  fixes after release require a new verified version rather than silently changing
  a device wrapper or tag. Acceptance: another clean installation can reproduce
  the corrected route without undocumented knowledge.
- [ ] **T17.6 — Record Gate B and operational handoff.** Save each device's
  release/profile/source/settings fingerprint, outcomes, observation duration and
  tested recovery route. Map evidence to Gate B and list any intentionally deferred
  schedule/support scope. Acceptance: actual upgrade and second-device operation
  proven; required T10–T16 gates and support claims consistent; update parent
  checkbox only when all required deployment evidence exists.

## Stopping and rollback

Use T15's documented triggers, including wrong fixture, unexpected levels,
settings loss, stale-confirmation defects or resource instability. Restore the
saved known-good release/settings and confirm physical readback. Unattended
software work may prepare wrappers/tests but cannot substitute for installation
observations or authorize flashing a live enclosure.

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
