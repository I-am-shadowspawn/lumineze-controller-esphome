# T15 — Hardware, resources and upgrade evidence

**Entry/dependencies:** T12–T14 software acceptance and recorded Gate A results.
Planning/instrumentation design can proceed now. **Delivery:** measured evidence
for each advertised profile and a rehearsed upgrade/recovery path.

## Bench protocol and limits

Use the established Pi Hut ESP32-C3 with JungleDawn/ProT5 and a serial recovery
route. Record board/lamp revisions, firmware SHA, ESPHome/ESP-IDF versions,
partition layout, topology, timezone, calibration and settings. Start on an
isolated bench. Do not flash a live enclosure under unattended implementation.
Three/four-fixture builds remain experimental unless separately measured.
Reuse Gate A and [T23 bench traces](t23-bench-validation.md) only when their exact
SHA/configuration and observations apply; new shared-code changes require a
focused rerun. Schedule does not automatically gain T23 capabilities.

Proposed test envelope to freeze in T15.1: one 24-hour normal run and a separate
one-hour fault/reconnect/OTA exercise per profile; at least 20 reconnect cycles.
Gate A/T23 physical work may supply applicable seasonal intervals. Record sample
cadence and worst transient, not just startup or an average. A firmware update
starts a new observation window for affected cases.

## Incremental deliveries

- [ ] **T15.1 — Freeze protocol and pass/fail budgets.** Write
  `docs/hardware-validation.md` with test IDs, sequence, observation periods,
  instrumentation and predeclared RAM/OTA/responsiveness limits. Proposed static
  OTA budget: app <=85% of its actual OTA partition; verify partition layout and
  OTA feasibility. Select runtime free-heap/largest-block floors from measured
  BLE/OTA workload requirements with explicit reserve, before candidate testing;
  if unavailable, mark the budget unresolved and block completion. Proposed
  response budgets: policy request <=one 10-second tick; physical delivery within
  configured dispatcher/transaction/retry timing, never a fixed instant claim.
  Acceptance: no unexplained resets/watchdogs or allocation failures, numeric
  budgets recorded before results, and stop/rollback conditions explicit.
- [ ] **T15.2 — Operational BLE/time fault matrix.** Run off/low/medium/high,
  calibration reduction, manual/auto transitions, group partial delivery, changed
  pending targets, mismatched/missing/stale report, power cycles, Wi-Fi/API loss,
  clock loss/recovery, disconnect and healthy-member progression. Acceptance:
  requested/completed/reported traces satisfy common policy, attempts bounded,
  no obsolete revival, off remains unknown without readback, HA loss does not
  prevent autonomous operation. Map applicable Gate A/T23 evidence explicitly.
- [ ] **T15.3 — Engine and development boundaries on-device.** Exercise seasonal
  golden cases and every representative schedule point/wrap/edit/startup/DST
  case; simulated snapshots cover rare dates but real-clock behavior also has
  live evidence. Check all four profiles and production entity omissions.
  Acceptance: T10 outputs match independent expected values; bench-output
  enablement and permanent limits cannot be bypassed; simulation resets off.
- [ ] **T15.4 — Resource/OTA soak.** Capture static sizes, minimum free heap,
  largest free block/fragmentation where available, BLE/API latency, OTA workload,
  resets/watchdogs and fault recovery for all profiles under comparable topology
  and reporting cadence. Document instrumentation overhead. Acceptance: frozen
  limits pass throughout the run; unsupported topology is not promoted from
  compile size; dual-engine feasibility is not inferred from separate builds.
- [ ] **T15.5 — Settings/identity migration matrix.** Test v1 known-good→generic,
  seasonal development→production, seasonal↔schedule, and upgrade within the
  same profile. Test label/group changes and fixture assignment fingerprint
  changes separately. Acceptance: compare before/after calibration, engine
  settings, entities and HA automations; expected resets/default-off documented;
  new/reassigned UV cannot inherit an old lamp's maximum. Interrupted preference
  writes preserve a valid schedule or reject it safely.
- [ ] **T15.6 — Recovery rehearsal and report.** Demonstrate OTA where supported,
  USB recovery, previous pinned firmware/settings restoration and autonomous
  operation afterward. Record storage downgrade limitations and any manual
  re-entry. Acceptance: each advertised profile has a result table, traces and
  explicit limitations; no unexplained regression remains; hand off a verified
  recovery runbook and final evidence SHAs to T16/T17.

## Stopping and rollback

Stop candidate testing for an unexpected nonzero output, wrong lamp assignment,
loss of bounded recovery, unexplained reset or resource-budget breach. Capture
trace and recover the bench using the saved known-good build. Fix defects in
reviewable increments and rerun affected cases; do not lower budgets after seeing
failures without an explicit reviewed rationale and a new test protocol.

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
