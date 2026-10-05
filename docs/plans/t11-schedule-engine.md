# T11 — Implement one schedule engine per build

**Entry:** T10 contract/vector set finalized. The owner explicitly authorized
isolated T11–T14 software work while Gate A remains open on 5 October 2026.
Hardware, stable release and live deployment gates remain unchanged.
**Dependencies:** T10, T09/Gate A. **Delivery:** schedule production/development
profiles using the existing generic fixture policy and BLE path.

## Observed seams and intended boundaries

`topology/controller-core.yaml` currently includes the seasonal engine; that
engine owns `evaluate_topology` and its 10-second interval. `ContextState` and
`topology_contexts` mix seasonal settings with shared outputs, and topology
validation currently accepts only `engine_family: seasonal`. These are actual
couplings to address, not an invitation to reuse seasonal entity IDs for schedules.

Separate a shared output envelope from engine-owned state. Preserve desired,
peak, curve, validity and simulation provenance used by conversion. For schedule
levels, publish desired=level/100, peak=1 and curve=desired so calibration is
applied once at the fixture boundary. Add a role-scoped transition revision only
for T10's Apply/step-boundary semantics, with zero/default behavior preserving
seasonal parity. Keep seasonal context settings/state absent in schedule firmware.

An engine-free orchestrator captures one selected provider snapshot, evaluates
the selected engine once per context, then runs policy. It owns the single tick.
Profiles compose exactly one engine and provider; schema/final validation must
agree with that selection. Do not embed schedules, MACs or interpolation in BLE.
Use fixed-size point records, pure bounded evaluation, and transactional active
snapshot storage. No host generator is required for Device Builder consumers.

T23 is merged but its UI is currently in the shared fixture fragment. Compose
seasonal temporary controls as an explicit capability rather than accidentally
exposing them in schedule profiles. Preserve seasonal entity IDs and behavior;
shared revocation/transport helpers remain common. Schedule support for temporary
lighting is a separate contract change, not implicit T11 scope.

## Incremental deliveries

- [x] **T11.1 — Mechanical engine boundary extraction.** Separate shared output
  records, seasonal private records and orchestrator/composition while retaining
  existing public aliases, preference identities and entities. Capture resolved
  inventories before/after. Acceptance: seasonal golden parity, both existing
  builds, generated provider isolation, policy/transport and T23 regressions
  pass; no schedule behavior in this increment.
- [x] **T11.2 — Pure schedule evaluator.** Implement the finalized T10 cyclic
  step/linear algorithm and validation in a small helper, with fixed capacity.
  Acceptance: every T10 vector passes, including exact points, midnight, disabled
  and sorted points, empty/invalid roles and DST/correction snapshots; no clock,
  preference, BLE or HA access inside the evaluator.
- [ ] **T11.3 — Runtime editor and persistence.** Add context/role schedule
  fragments, staged HA controls, atomic Apply/Cancel, active revision/status and
  versioned integrity validation. If the platform cannot atomically save the
  bounded record, use two records plus a validated commit selection and test
  power-loss recovery. Acceptance: rejected/half-edited/corrupt snapshots never
  replace active output; reboot restores the last complete valid schedule;
  automatic/manual controls still start off and no implicit activation occurs.
- [ ] **T11.4 — Generic composition and authorization.** Add schedule entry
  points, `context-schedule.yaml` and real/development build fixtures. Extend
  schema to schedule family and enforce matching context fragments, role routing
  and single-engine ownership. Implement one-time transition authorization,
  stale-write revocation and current-time reevaluation. Acceptance: swapped,
  repeated and sparse fixtures work; min-change bypass does not reset retries;
  manual, automatic-off, safe-off and invalid-clock cases use common policy.
- [ ] **T11.5 — Capability and diagnostic isolation.** Expose schedule status
  with the schedule engine; generic health entities remain engine independent.
  Compose T23 controls only for seasonal profiles. Development simulation uses
  the existing non-restoring input/bench gate. Acceptance: schedule production
  has no seasonal private state/entities or development controls; seasonal
  production retains T23; simulated output cannot escape the common bench gate.
- [ ] **T11.6 — Build and behavioral handoff.** Validate/compile both schedule
  profiles and rerun seasonal/T23 regressions. Exercise the actual production
  policy with schedule contexts, calibration reduction, Apply during a write,
  reconnect, invalid restore and shared groups. Record ESP32-C3 sizes, resolved
  inventories and required T15 physical cases. Acceptance: software results map
  to every T10 case; physical evidence is explicitly pending, not inferred.

## Migration and rollback

Preserve legacy entry points and seasonal settings. Engine changes require a
rebuild plus explicit commissioning; schedules never reinterpret seasonal
preferences. Record new persistence schema and recovery/export before testing.
Revert extraction independently if baseline parity fails. Incompatible storage
requires explicit reset/re-entry instructions; no automatic lamp enabling.

## Execution and evidence rules

Use the [delivery index](t10-t17-delivery-index.md) for gate definitions and the
baseline. The checkboxes below are the canonical incremental tracker for this
task. Complete each increment in a separate reviewable commit after its checks
pass. Record source SHA, files, commands/results, evidence links, deviations and
remaining work beside that increment. Proposed filenames may change; ownership
and acceptance criteria may not silently change. Do not mark implementation or
hardware increments complete because this plan exists.

**Progress:** T11.1 extraction and T11.2 pure evaluator complete; T11.3 is next. Physical Gate A/T23 evidence remains pending.

## Execution record

### T11.1 — complete

Branch `implementation/t11-t17`, source `c250604`, ESPHome 2026.9.0. Owner
reply: “Proceed with software; keep hardware gates open.” Created common
`orchestrator.yaml`, moved selected-engine composition into seasonal profiles,
and split `SeasonalSettings` into an engine-owned header/global. Shared
`ContextState` now contains output state only. Public entity IDs, names, defaults,
restore settings and compatibility aliases retain their resolved baseline.

Evidence: both generic seasonal ESP32-C3 profiles compile; 1,600 seasonal targets,
provider parity, T23 policy, fixture conversion/transport, safe-off and timeout
checks pass. Input isolation and 17 topology schema cases pass; diagnostic
inventories pass. `scripts/check_seasonal_inventory.py` compares both resolved
profiles against source `c250604`'s dummy-fixture entity/settings inventory and
runs in CI. No persisted keys/calibration mapping changed. Full logs are local
`/tmp/t11-1-{production,development}-build.log`; CI reruns the committed checks.
Gate A remains open. Next increment: T11.2 pure evaluator and T10 numeric cases.

### T11.2 — complete

Source: `0e85b29`. Added bounded `schedule_logic.h`: atomic staged-field
validation before narrowing, cyclic step/linear evaluation, sorted enabled-point
lookup without mutating editor slots, explicit validity and stable segment slot.
The helper has no clocks, preferences, HA or BLE dependency. No schedule code is
composed into firmware yet.

`scripts/check_schedule_cases.py` compiles and runs the checked-in T10 oracle
against the helper and existing fixture converter: 56 outputs, 22 validations
and eight exact target conversions pass under C++17 with warnings as errors.
Rejected validation preserves the destination. CI runs the harness. T10's 21
policy/HA and 13 persistence scenarios are intentionally deferred to their
owning increments, not counted as passed from JSON parsing. `git diff --check`
passes. Next: T11.3 editor, two-bank durable storage and fault-injection coverage.

### T11.3 — in progress

- [x] **T11.3a — Durable record/storage core.** `schedule_store.h` implements
  the specified packed schema, independent two-bank restore, modulo revisions,
  context-atomic validation, Unchanged/Cancel, deferred activation and uncertain
  storage locking. `schedule_preferences.h` allocates each backend once and
  requires flush/readback before success. No restoring per-field editor values.
- [ ] **T11.3b — HA editor and lifecycle composition.** Next: context/role/point
  fragments, stable entity IDs, Apply/Cancel/status and boot publication. Validate
  and compile a schedule composition and prove UI rejection/restore behavior.

T11.3a evidence: `scripts/check_schedule_storage.py` compiles/runs the C++ storage
fault harness, covering the 13 T10 persistence scenarios plus context rejection,
all 88 replacement-write prefix lengths, every single-byte corruption, malformed
checksummed fields and uncertain flush/readback. Independent zlib verifies the
87-byte record CRC. T10's 86 numeric/validation/conversion cases still pass.
A temporary compile-only dummy topology included the real ESPHome adapter and
restore call; the ESP32-C3 firmware compiled successfully (log:
`/tmp/t11-3-storage-adapter-build.log`). The temporary fixture was removed and
never flashed. CI now runs the fault harness. No hardware persistence proof is
claimed; that remains T15. T11.3 stays unchecked until editor integration passes.
