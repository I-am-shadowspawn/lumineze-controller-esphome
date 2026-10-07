# Static fixture topology controller

The generic seasonal entry points are `packages/seasonal-production.yaml` and
`packages/seasonal-development.yaml`. The schedule equivalents are
`packages/schedule-production.yaml` and
`packages/schedule-development.yaml`; all four have software build evidence,
while Gate A and T15 physical evidence remain open. The older
`packages/lumineze-topology.yaml` and `packages/lumineze-topology-development.yaml`
paths remain compatibility aliases. The existing
`packages/lumineze-controller.yaml` path still resolves to the v1 two-product
configuration, now explicitly composed through
`packages/compat/legacy-two-fixture.yaml`. A generic build is a **new
installation/migration**; it does not import v1 Home Assistant entities or
settings automatically. Keep a known-good v1 tag and its private YAML for
recovery.

Production uses the real-clock snapshot provider. Development topologies use
`packages/seasonal-development.yaml` with
`input_provider: development`; their simulation enable and simulated-output
switches reset off, and simulated automatic output remains calculation-only
until explicitly enabled for bench use. The fixed two-fixture development
composition is `packages/lumineze-controller-development.yaml`. The seasonal
algorithm consumes the same captured snapshot in either profile, while
transaction, retry and safety timers remain monotonic real-time clocks.

## Device Builder composition

Choose one of the four profile-named wrappers in `example/` and provide its
private secrets. Pin
`controller_ref` to the same tested Git commit or release tag for both the
package and `lumineze_topology` external component. The example deliberately
places ProT5 in slot 0 and JungleDawn in slot 1. Slot is storage/arbiter order,
not a product or role. The remote `files` list includes:

1. One common controller package.
2. One `context-seasonal.yaml` or `context-schedule.yaml` instance per context
   (one or two). Schedule builds also include one role editor for each used
   visible/UV role.
3. One `group.yaml` instance per group (one to four).
4. One `fixture-luminize.yaml` (seasonal) or
   `fixture-luminize-schedule.yaml` (schedule) instance per **enabled** fixture
   (one to four). Development builds add one matching fixture diagnostic
   fragment per enabled fixture.

Repeat a fragment with distinct `vars` as needed. Disabled/reserved descriptors
stay in `lumineze_topology.fixtures` with only `id`, `slot`, `enabled: false` and
optional `location`; omit their fixture package entirely. The validator checks
that enabled descriptor IDs and MACs match exactly the static BLE clients and
transaction scripts. It rejects invalid IDs, slots, products, roles, references,
duplicate/placeholder MACs, unused groups/contexts, a missing adapter, and
insufficient BLE connection allocation during normal `esphome config`, including
Device Builder remote imports. The MAC value is never included in a custom
validation error.

Three or four enabled fixtures require `allow_experimental_topology: true` and
`ble_connection_slots` equal to the fixture count. ESPHome 2026.9.0 reserves a
connection slot for every declared BLE client even though the controller sends
one transaction at a time. This opt-in allows a software build; it does not
establish reliable four-lamp operation on ESP32-C3 hardware.

## Runtime behavior

- A context holds one independent set of seasonal settings and emits `visible`
  and `uv` fractions. The engine reads the clock once per evaluation, evaluates
  each context once, then evaluates groups and members. No context holds a MAC,
  slot, fixture maximum or BLE retry state.
- A group selects one context output. Group automatic/manual enable is
  independent even when groups share a context. Group manual level is **percent
  of each member's calibrated maximum**. One demand of 72% produces 72% for a
  fixture capped at 100%, and 43% for a fixture capped at 60%.
- Fixture manual level is an **absolute lamp percentage**, capped by that
  fixture's own maximum. Priority is invalid-time safety, fixture manual,
  group manual, group automatic, then hold. A group-off action disables its
  controls, releases member overrides and queues 0% to each member; controller
  off does so for all groups. Fixture off activates that fixture's 0% local
  override. An off request is a command, not proof that an unavailable lamp is
  dark. Group/controller off remains requested while controls stay disabled;
  a deliberate manual request or automatic re-enable supersedes it on the next
  policy evaluation. Active invalid-time safety cannot be overridden.
- Targets have a source, group revision and per-fixture generation. Repeated
  unchanged automatic evaluations do not reset retry backoff. Cap reductions,
  manual and safety commands bypass the usual automatic change threshold.
  Invalid/non-finite nonzero demands are rejected; safety-off works with an
  invalid maximum. The generic package has no simulation input or test-level
  production control. Each fixture's automatic preview uses the same
  conversion routine as an operational automatic request.
- A single dispatcher selects enabled slots round-robin. Each fixture owns its
  own pending/in-flight/completed/reported state and retry counters. The
  adapter template keeps the v1 LuminEZE frames and delays. Notification
  readback is recorded separately from successful writes. Group diagnostics
  report confirmed member counts and partial delivery.

## Calibration, identity and migration

New JungleDawn fixtures start at 100%; new ProT5 fixtures start at 0% and must
be calibrated before nonzero UV output. Calibrated maximum is stored using a
preference key derived from fixture ID, slot, product and MAC. A replacement,
type change or slot reassignment therefore starts from its product default;
group reassignment or label edit retains the calibration. Group automatic and
manual controls start off after every boot, including a membership change;
fixture manual overrides also start off. Enable automatic control deliberately
after checking the new topology and calibration.

The generic Home Assistant entities use group, context and fixture IDs. Stable
IDs are required for stable settings. Seasonal setting and minimum-change
names derive from stable IDs so display-label changes do not reset those
preferences. Display-only diagnostic labels may change their HA entity IDs.
The old and new inventories differ: do not point an existing flashed controller
at the generic entry expecting a silent settings migration. Export the current
HA values first, create the intended topology and calibrate every physical
fixture explicitly. The legacy package's resolved `ci/controller.yaml` config
was byte-for-byte identical before and after the compatibility wrapper change.

| v1 entity/settings owner | Generic owner |
| --- | --- |
| Shared solar settings | One chosen seasonal context |
| JungleDawn/ProT5 automatic switches | Visible/UV groups |
| JungleDawn/ProT5 manual level and override | Named fixtures |
| JungleDawn/ProT5 maximum and minimum change | Named physical fixtures |
| BLE interval/retry settings | One common dispatcher |

## Software evidence and external gate

ESPHome is pinned in `requirements-ci.txt` to 2026.9.0. Local package
composition, repeated remote Git package files and same-ref remote external
component loading all passed `esphome config` and firmware compilation. The
topology validator is exercised by `scripts/check_topology_schema.py`; nine
operational shapes are exercised by `scripts/check_topology_matrix.py`.
`tests/test_fixture_logic.cpp` calls the same conversion and transaction
transition helpers used by production lambdas. The legacy resolved config is
unchanged, and its firmware still compiles.
`scripts/check_seasonal_parity.py` compiles the production seasonal lambda and
matches 1,600 integer targets against the v1 formula across dates, times,
contexts and fixture maxima. `scripts/check_protocol_trace.py` compares both
v1 adapter frames/UUIDs/delays with the generic adapter.

Representative local compile footprints (ESP32-C3, ESP-IDF 5.5.5, same
application partition):

| Build | Image | Static RAM | Flash use |
| --- | ---: | ---: | ---: |
| Legacy two-product CI | 1,442,368 B | 149,044 B | 78.6% |
| Generic two visible fixtures | 1,258,352 B | 145,000 B | 68.6% |
| Generic four fixtures/two contexts | 1,280,320 B | 153,248 B | 69.8% |

These images expose different diagnostic inventories, so size differences are
not an optimization claim. No real lamp was flashed for this refactor. Minimum
runtime heap, BLE reconnect/timeout behavior, watchdog stability and Wi-Fi/API
responsiveness need physical testing before three/four fixtures are described
as production-supported. A generated C++ build cannot prove an unavailable
lamp received safe-off or that notification timing is reliable on hardware.
