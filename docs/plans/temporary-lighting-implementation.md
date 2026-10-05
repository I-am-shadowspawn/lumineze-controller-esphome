# Implementation plan: temporary lighting controls

**Implementation status:** the software work is on branch `t23-codex`.
Deterministic policy tests, both seasonal profile builds, no-override parity,
and generated-input isolation pass. The final ESP32-C3 lamp/readback bench
acceptance remains outstanding.

**Dependency/status:** T09 is merged. T23 software is implemented on its own
branch while Gate A's physical evidence remains pending; keep T23 open until
that evidence is recorded. It does not depend on T10–T22, and its first release
covers only the supported generic seasonal production/development profiles. The
[requirements](../temporary-lighting-requirements.md) are the behavior
contract; resolve any T09 interface renames against that contract before
changing firmware.

## 1. Capture the T09 baseline

- Start from the merged T09 commit and record the exact seasonal entry points,
  fixture-policy contract, entity IDs, CI commands and known hardware limits.
- Reproduce the T09 production/development compile and seasonal parity result
  before changing common control. Keep a no-override golden fixture so later
  diffs show that ordinary curve output has not changed.
- Confirm whether the supported seasonal entry points still use the generic
  fixture/group/context packages. If T09 changes composition, adapt the paths
  below while retaining per-fixture state and one common dispatch path.

## 2. Add a small per-fixture state machine

- Store `none`, `daily_max` or `timed_fixed` plus a generation/revision in the
  fixture's volatile state. Store active maximum and its local date, or active
  fixed level and monotonic start/duration. Do not persist active mode or
  deadline. Keep staged Home Assistant values separate from active snapshots.
- Define pure transition helpers for Apply, Start, Cancel, local-date change,
  descending crossing, elapsed duration and higher-priority control events.
  Compare the normal final integer automatic target with the active maximum.
  Use rollover-safe elapsed arithmetic for the timer.
- Retain a candidate target and an accepted target separately. The cap gate
  suppresses higher automatic submissions while the seasonal engine continues
  evaluating. Treat an activation correction and dusk release as explicit
  events so minimum-change filtering cannot hide them.

Likely owners after T09: `components/lumineze_topology/runtime_types.h` for
state, `components/lumineze_topology/fixture_logic.h` for pure policy helpers,
and `packages/topology/fixture-policy.yaml` for arbitration. Do not put this
state in the seasonal formula or BLE transaction script.

## 3. Integrate with the existing control path

- Resolve the normal automatic target using the current conversion routine,
  then pass it through the temporary policy before accepting a fixture target.
  Keep permanent calibration, invalid-output rejection, simulation gating,
  safety and commissioning checks in their existing order.
- Give timed fixed output an explicit source/revision for diagnostics and
  pending-request authorization. On expiry or cancel, revoke that source's
  pending/retry generation and immediately evaluate the current real snapshot.
- Reuse dispatcher queue coalescing and token checks. Never write BLE directly
  from a Home Assistant button, timer or seasonal calculation. Handle a
  correction/release behind an in-flight write by queueing the newer
  authorized generation and reporting the interval as pending.
- Clear temporary state when a manual override is activated, automatic is
  turned off, safe-off is requested or live time becomes invalid. Do not let an
  old completion, retry or reconnect restore it. Preserve independent fixtures
  and group delivery accounting.

## 4. Expose and compose Home Assistant controls

- Add the staged numbers, Apply/Start/Cancel buttons and operational status
  entities listed in the requirements once per enabled fixture. Keep entity
  IDs stable and fixture-scoped. Defaults and active state must be non-restoring.
- Validate range, finite values, commissioning, live date and automatic/manual
  preconditions at action time. Publish an explicit rejection reason. Snapshot
  valid staged values only on Apply or Start.
- Include the controls in both T09 seasonal profiles. No development test
  entity should leak into production. Document the user workflow and the fact
  that Cancel can immediately return a lamp to a higher current curve level.
- Leave the legacy v1 package and schedule engine untouched in this task.
  Reuse the same common policy for schedule only when that engine is later
  introduced and has its own acceptance cases.

## 5. Verify the contract

- Add deterministic cases for the rising/holding/descending sequence,
  equality and skipped equality, never-reached cap, application above cap,
  immediate reduction, local-date expiration and clock correction.
- Cover fixed-level Start/restart/expiry with 0%, a calibrated limit and
  monotonic-counter rollover; check HA loss, reboot, invalid duration and
  invalid clock. Verify one fixture in a shared group does not affect another.
- Exercise stale pending/in-flight completions, retry after disconnect and
  readback mismatch. Assert each temporary transition has one current
  authorized generation and no direct BLE path.
- Compile both seasonal profiles, compare entity inventories and rerun
  no-override seasonal parity. If common policy changes affect other supported
  profiles, compile their fixtures too. On the ESP32-C3 bench, confirm the
  rising cap, dusk release, timed return and requested/completed/reported
  distinction with a real lamp.

## Delivery boundary

Mark T23 complete only when the requirements' acceptance cases and bench
evidence are recorded. Keep this plan and requirement separate from T09's
parity gate; the new behavior is an intentional post-T09 feature change.

## Review hardening and bench handoff

Duration validation checks finite 0.25–24-hour values on quarter-hour steps;
the pure timer helper also rejects millisecond durations off that step. The
historical exceedance flag alone triggers the first at/below-cap release,
independent of diagnostic status. This explicit transition bypasses
minimum-change, avoiding duplicate confirmed targets.

Every accepted temporary transition invalidates prior authorization and
readback freshness before policy reevaluation. Same-level restarts also receive
a new generation. Completion of an obsolete transaction records physical
history without clearing the newer queue or confirming its readback. Corrective
cap requests retain bounded retry budgets across evaluations. An above-cap fresh
report is retained as a correction reason across activation; completed writes
without readback stay unconfirmed. Unsolicited reports cannot inherit an older
freshness flag. Apply/Start
refresh the seasonal snapshot and check valid calibration before activation.

`tests/test_fixture_logic.cpp` exercises pure transition/transport cases;
`scripts/check_temporary_policy.py` executes the production YAML policy lambda
against controlled seasonal inputs and simulated BLE outcomes. CI runs both.
The [bench session](t23-bench-validation.md) defines hardware setup, traces,
full rise/hold/descent and fixed-duration sequences, interruptions, readback
ordering and the evidence required to close T23. Physical evidence is pending.
