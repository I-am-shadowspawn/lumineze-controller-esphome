# T10 — Configurable daily schedule contract

**Status:** specification complete; schedule firmware is not implemented.
Source audit: development `e786bee`, ESPHome CI pin `2026.9.0`, 5 October 2026.
Gate A/T09 and T23 physical acceptance remain pending. The owner requested T10
completion while those tests proceed; T11 firmware implementation still waits
for Gate A. Relevant hardware findings require an explicit contract/vector
revision before T11, not an implicit behavior change.

## 1. Scope, decisions and current seams

A schedule build contains one schedule engine, one selected input provider and
one common policy/dispatch path. Up to two contexts independently emit `visible`
and `uv` fractions; groups select those outputs and fixtures consume group
requests. Slots do not imply product, role or schedule. Repeated products and
shared contexts are supported by the existing topology contract. Runtime changes
cannot change fixture membership, MACs, context identity or engine family.

| Decision | Settled rule and reason |
| --- | --- |
| Capacity | Eight point slots per role/context; bounded storage and an explicit daily shape |
| Sharing | Independent schedule for each context/role; sharing occurs through groups, never inferred from products |
| Interpolation | Role-wide `step` or `linear`, selected at runtime through staged settings |
| Ramps | Linear segments between point levels; no separate ramp-duration/window model |
| Units | Integer configured level 0–100%, relative to each fixture's calibrated maximum |
| Time | Repeating local wall-clock day; coherent provider snapshot includes fractional minutes |
| Overnight | Cyclic last-to-first segment; explicit zero points produce an off interval |
| Edit activation | Complete context Apply, including both roles; rejected edits leave active state untouched |
| Restore | Only validated active snapshots restore; groups/manual controls remain off at boot |
| Scope exclusions | Weekly/holiday calendars, dynamic topology, runtime engine switching and T23 schedule support |

Absolute lamp percentages would bypass the established group/fixture calibration
contract; use fixture manual controls for that operation. A one-point constant
schedule is excluded to keep the same minimum topology for both interpolation
modes: use two equal-level points for constant output. Event-triggered replay is
excluded because it depends on observing every event and makes startup/DST
ambiguous. The legacy seasonal package is unchanged.

### Current-code audit and T11 handoff

| Owner / current files | Observed contract | Required schedule adaptation |
| --- | --- | --- |
| `components/lumineze_topology/__init__.py` | Family validation accepts only seasonal; explicit contexts/groups/product-role routing | Permit schedule with matching fragments, not merely a new family string |
| `runtime_types.h`, `topology/base.yaml` | `ContextState` combines seasonal parameters and common output arrays | Separate engine-private parameters from shared role output; no seasonal private state in schedule builds |
| `topology/seasonal-engine.yaml`, `controller-core.yaml` | Seasonal engine owns `evaluate_topology`, provider call and 10-second tick | Shared orchestrator owns snapshot→selected engine→policy, once per context |
| `fixture_logic.h`, `fixture-policy.yaml` | Automatic fractions, peak/curve conversion, fixture maximum, thresholds and arbitration | Publish desired=level/100, peak=1, curve=desired; scale once; add bounded transition intent for Apply/step edges |
| `group.yaml`, `fixture-luminize.yaml` | Group manual is relative; fixture manual absolute; controls default off at boot | Keep those semantics, preference identities and physical calibration keys |
| `transport_logic.h`, `dispatcher.yaml` | Request generations, transaction tokens, bounded retries, completed/reported distinction | Reuse authorization; schedule cannot call BLE or revive obsolete generations |
| `fixture-luminize.yaml`, T23 helpers | Seasonal temporary UI currently shares fixture fragment | Explicit seasonal-only capability composition; schedule has no T23 actions |

### Point validation and used roles

A context has exactly eight staged slots for each used role. Slot indices 1–8
are editor identity only. Each slot stores enabled Boolean, integer minute
0–1439, and integer level 0–100. Reject malformed, fractional, non-finite or
out-of-range fields even on disabled slots; disabling does not sanitize bad data.
Duplicate times among disabled slots are allowed. Enabled times must be unique.
Apply sorts enabled points by time; out-of-order slot edits are valid. Mode must
be exactly `step` or `linear`. More than eight slots is rejected.

A role is used if any declared group consumes it. Every used role needs 2–8
enabled points. An unused role has no editor entities, may have zero enabled
points, and emits invalid output; no group may consume it without a rebuild and
valid schedule. Unknown role names are rejected. Context Apply validates all used
roles atomically; a bad UV edit cannot partially apply a valid visible edit.
Validity must be role-aware: an unused invalid output cannot invalidate the
context's configured visible output. Context active-valid aggregates used roles
only; topology validation prevents a group consuming an unused role.
Two all-zero points are valid and mean off, not invalid output. Disabling a point
removes it from interpolation; there is no separate disabled-window switch.

### Bounded interface/storage budget

Per used role: eight enable switches, eight minute numbers, eight level numbers
and one mode select = 25 staged entities. Per context: Apply/Cancel buttons,
status text, active revision sensor, active-valid and dirty indicators = six.
One visible-only context therefore adds 31 entities; one dual-role context 56;
two dual-role contexts 112. These are upper bounds, not measured ESP32-C3 resource
support. Unused roles contribute no entities. Editor labels include role and slot
and make the relative-level and minute-after-midnight units explicit.

Point payload is four bytes (enabled byte, little-endian uint16 minute, level
byte); eight points plus one mode byte is 33 bytes per role. The complete record
specified below is 87 bytes; two records/context require 174 payload bytes
(348 across two contexts), excluding preference backend overhead. Three bounded
working copies of point data across two dual-role contexts use 384 point bytes,
plus metadata and output records; budget the schedule's explicit data records
within 1 KiB. HA entities, framework allocation and buffers are additional and
must be compiled/measured in T11/T15. If those checks fail, revise capacity and
vectors explicitly before advertising schedule support.

## 2. Evaluation, boundaries and clock behavior

Let `t` be local minutes after midnight including seconds/60, in `[0,1440)`.
Reject invalid provider calendar/clock, non-finite `t`, or out-of-range `t`;
never clamp a malformed time into a valid point. Leap days use the same daily
schedule. Validity and simulated provenance come from one captured snapshot.

For sorted enabled points, find the last point at/before `t` and the next point.
If no earlier point exists, use the last point on the previous day. After the
last point, use the first on the next day. Extend times by ±1440 for that one
segment. A segment never has zero duration because enabled times are unique.

- **Step:** output the earlier point's level until the next point. At an exact
  point, use the new point's level, including exact minute zero.
- **Linear:** interpolate from earlier to next: earlier level plus their level
  difference times elapsed segment minutes divided by segment duration.
  Do not round the interpolated percentage before the fixture boundary.
- Both modes evaluate from the current time; boot does not replay morning points.
  Before/after endpoints are cyclic, not an implicit off or permanently held tail.

### Concrete visible example

Enabled points: 08:00=0, 10:00=100, 18:00=100, 20:00=0. Both modes are 0 overnight.
The table is the logical percent of each fixture's maximum, before calibration.

| Local time | Linear | Step |
| --- | ---: | ---: |
| 00:00 / 07:59 | 0 | 0 |
| 08:00 | 0 | 0 |
| 08:30 | 25 | 0 |
| 09:00 | 50 | 0 |
| 09:00:30 | 50.4166666667 | 0 |
| 10:00 | 100 | 100 |
| 12:00 / 18:00 | 100 | 100 |
| 19:00 | 50 | 100 |
| 20:00 / 23:59 | 0 | 0 |

### Concrete UV example

Enabled points: 09:00=0, 10:00=80, 16:00=80, 17:00=0.

| Local time | Linear | Step |
| --- | ---: | ---: |
| 08:00 / 09:00 | 0 | 0 |
| 09:30 | 40 | 0 |
| 10:00 / 12:00 / 16:00 | 80 | 80 |
| 16:30 | 40 | 80 |
| 17:00 / 00:00 | 0 | 0 |

With a commissioned UV maximum of 50%, the linear 09:30 target is 20% lamp
output. With the new ProT5 default maximum of 0%, it remains 0%. No schedule
parameter constitutes calibration or exposure guidance.

### Midnight and disabled-point examples

Points 02:00=0 and 22:00=40 give linear 23:00=30, 00:00=20, 01:00=10, 02:00=0;
step is 40 throughout the wrapping segment until exact 02:00. The daytime
linear segment ramps 0→40 over 20 hours. Add explicit zero boundary points if
that daytime ramp is unwanted. A point at 00:00 is allowed; 24:00 is not.

For 08:00=0, disabled 09:00=100, 10:00=0, output at 09:00 is 0 in either mode.
Disabling an endpoint may lengthen a segment across midnight; Apply previews
validation but must not silently add an off window. Unordered slots 20:00=0,
10:00=100, 08:00=0, 18:00=100 are equivalent to the visible example after sorting.

### DST, corrections, clock loss and missed evaluations

| Situation | Required output/application |
| --- | --- |
| Spring clock jumps over a point | Evaluate the new local time/segment; do not emit every skipped point |
| Autumn local hour repeats | Evaluate that hour again; the same local timestamp has the same schedule output |
| Forward/backward correction | Evaluate corrected time immediately on the next evaluation; no catch-up queue |
| Startup part-way through day | Restore validated active settings, evaluate now, leave groups off until deliberate enable |
| Missed evaluation/tick | Recompute now, not an accumulated ramp increment |
| Date change/leap day | Same repeating schedule, continuous cyclic midnight segment; date alone is not an output event |
| Invalid live clock | Invalidate automatic schedule output and revoke automatic retries; shared invalid-clock safety applies |
| Invalid simulated clock | Calculation error and automatic output blocked; do not misclassify it as live-clock safety |
| Return from simulation to live | Fresh live evaluation replaces authorized simulated output, including within normal threshold |

Example DST-style snapshots on a linear schedule 01:00=0, 03:00=100, 23:00=0:
01:30 gives 25; a jump to 03:00 gives 100. A backward correction from 02:30
(75) to 01:30 (25) yields 25, even if that wall-clock time occurred earlier.
The skipped/repeated-hour size depends on the configured timezone; the algorithm
uses the provider's current local snapshot and does not hardcode a one-hour gap.

### Evaluation and transport timing

Use the existing 10-second engine/policy interval, with immediate reevaluation
on Apply and relevant common control/time-provider events. A time-sync callback
must request a fresh evaluation; timers for retries, uptime grace and transactions
stay monotonic. Output is an authorization, not instantaneous physical delivery:
BLE spacing, active transaction completion and retry delays still apply.

Linear intermediate values use the existing per-fixture minimum-change filter.
A changed **step segment**, accepted Apply, recovery to valid live output or
return from simulation requests one explicit reevaluation, bypassing that filter
when the final target changes. Repeated evaluations of the same segment cannot
reset retry budgets. Skipping several step segments requests only the current
segment; equal-level adjacent steps create no duplicate confirmed command.
Transition identity is role-scoped and distinct from the evaluation revision.

## 3. HA editor, activation, persistence and common control

### Entity and action contract

`<context>` means the stable configured context ID; `<role>` is visible or uv;
`<n>` is slot 1–8. IDs and operational editor names use these stable identifiers,
not the display label, physical slot, MAC or product. Labels may provide a
friendly explanation but must not alter preference identity.

| Entity ID pattern | Kind / values | Behavior |
| --- | --- | --- |
| `<context>_<role>_point_<n>_enabled` | Boolean switch | Stage inclusion only |
| `<context>_<role>_point_<n>_minute` | Number 0–1439, step 1 | Local minutes after midnight; stage only |
| `<context>_<role>_point_<n>_level` | Number 0–100, step 1 | Percent of fixture maximum; stage only |
| `<context>_<role>_schedule_mode` | Select `step`, `linear` | Stage interpolation for the role |
| `<context>_apply_schedule` | Button | Validate and commit the entire context |
| `<context>_cancel_schedule_edits` | Button | Reload staging from active or empty defaults; no output change |
| `<context>_schedule_status` | Text | Active/unconfigured/editing or precise rejection/storage reason |
| `<context>_schedule_revision` | Text sensor, decimal uint32 | Last durably committed revision; 0 when absent |
| `<context>_schedule_valid` | Boolean sensor | All used roles have a valid active snapshot |
| `<context>_schedule_dirty` | Boolean sensor | Staged data differs from active snapshot/defaults |

Production includes these operational controls. Development includes the same
controls plus the existing non-restoring simulated-input and bench-output gate.
Simulation cannot activate itself through restore/API reconnect. T23 temporary
controls are absent from schedule builds. Engine-specific preview diagnostics
may be added in development; they must use the active snapshot, clearly separate
from staged values and requested/completed/reported lamp levels.

### Apply/Cancel state transitions

1. Freeze one complete staged context snapshot; serialize Apply/Cancel/editor
   mutation with this operation so later edits cannot alter the captured data.
2. Validate schema, used roles, types/ranges, capacity and unique enabled times.
   On invalid data, keep active snapshot/revision and all pending requests intact;
   perform no preference write. Preserve staging for correction. Report role,
   point and reason (for example `Rejected: uv duplicate enabled minute 600`).
3. Normalize a bounded sorted evaluation copy while retaining stable editor slots
   in the persisted record. If the complete staged record equals active,
   return `Unchanged`: no flash write, revision increment or authorization reset.
4. Durably store and verify the new complete record. After known successful
   persistence, publish it atomically as active and increment revision, then
   immediately evaluate one fresh snapshot. Never publish half a role/context.
5. Apply preserves automatic/manual enable states; it never turns groups on.
   It is permitted while groups are disabled, manual is active or clock is
   invalid, because validating a daily schedule is independent of current time.
   Operational gates may consequently hold output or issue safety-off.
6. Replace obsolete automatic pending/retry generations for affected groups only.
   A new final target or source gets current authorization. A revoked identical
   pending target still needs a replacement generation; an identical already
   confirmed target needs no duplicate write. An old in-flight write may finish
   physically but cannot restore its request or confirm the newer decision.
   Keep retries bounded across unchanged evaluations. Manual/safety requests are
   not revoked by a schedule edit.
7. Cancel Edits discards staging changes and rejection text, loading active
   values; with no active snapshot, load mode `step` and all slots disabled at
   minute/level 0. Cancel Edits is not Cancel Temporary Lighting and sends no BLE
   command. Switching HA connections never acts as Apply.

The revision is represented as decimal text to preserve exact uint32 identity,
including rollover, without a float sensor's precision limit. Active-valid means
validated stored settings, not valid current clock or physical confirmation.

Active output continues during staging. A rejected action's diagnostic does not
mean the active schedule is invalid. Status distinguishes active revision from
staged error, for example `Active revision 7; rejected uv point 3 level`.
Dirty remains true after a rejected Apply and false after successful Apply,
Unchanged or Cancel. Editor mutation after a captured Apply appears as new dirty
staging after publication; it cannot alter the saved snapshot.

### Persistence and reboot contract

Use two independent bounded preference records per context, preserving the older
valid record until the newer one has been written/flushed/verified. This is a
storage requirement for T11 to prove on the pinned backend, not a claim that
multiple ESPHome numbers restore atomically. No per-field restoring staged number
may be used as the active schedule.

Schema 1 encoding, packed bytes without native-struct padding:

| Field | Bytes / encoding |
| --- | --- |
| Magic | 4 literal bytes `LZSC` |
| Schema | 2, little-endian uint16 = 1 |
| Record length | 2, little-endian uint16 = 87 |
| Revision | 4, little-endian uint32, nonzero |
| Context fingerprint | 4, little-endian first four SHA-256 bytes of `lumineze-schedule-v1\|<context-id>\|<used-role-mask>`; substitute 1 if zero |
| Used-role mask | 1; visible bit 0, uv bit 1; no other bits |
| Visible role | 33: mode byte (0 step, 1 linear), then eight 4-byte slot records |
| UV role | 33, same encoding |
| Checksum | 4, little-endian IEEE CRC-32 of preceding 83 bytes |

Each slot encodes enabled 0/1 byte, minute uint16 little-endian and level byte.
An unused role has canonical step mode and all disabled zero slots; it has no
entities or valid output. Validate record length, magic, CRC, fingerprint, schema
and every field before evaluation. CRC detects damage, not malicious changes.
Preference keys use a distinct schedule namespace plus context ID, role mask and
bank index; detect key collisions against other generated preferences. Renaming
a context or changing its used-role mask invalidates old schedule restoration.
Label/group/fixture changes that preserve context ID and role mask retain the
schedule; fixture calibration still follows its physical assignment fingerprint.

Recover the newest complete valid record; a torn/corrupt newest record falls
back to the older valid record. Revision starts at 1; increment modulo uint32,
skipping 0. Compare revisions by a modulo difference strictly between 0 and
2^31; equal revisions require identical payloads, otherwise reject the pair.
A half-range ambiguous pair is rejected. No valid record means unconfigured,
invalid automatic output and staging defaults. Unknown schema is never guessed
or interpreted as seasonal preferences. Loading valid active data does not enable
groups or restore fixture/group manual actions.

Apply acknowledges success only after durable storage and active publication.
A definitely failed write leaves the older record and active snapshot unchanged.
If persistence outcome cannot be established (including power loss before the
response), report `Storage outcome unknown; reboot/reload before Apply` rather
than claiming rejection or success; block further Apply until recovery selects
a valid record. Reboot may restore either the previous complete record or the
new complete record if that write finished. It must never restore a mixture.
An interrupted/unacknowledged operation has this explicit recovery rule; invalid
validation rejection always leaves persistence untouched. T11 must fault-test
these cases and its chosen preference flush/readback mechanism.

Only complete active settings persist. Staging is repopulated from active on
boot, losing uncommitted edits. Manual, transaction, simulation and temporary
state remain volatile. Upgrades within schema 1 preserve compatible records;
an incompatible future schema requires explicit export/migration. Downgrades
that cannot read the active schema start unconfigured with controls off.
Keep a private exported schedule/settings record for rollback and re-entry;
never overwrite seasonal calibration or automatically enable output on update.

### Common policy and final lamp target

Schedule output is a finite fraction `desired = interpolated_percent / 100`,
with `peak = 1`, `curve = desired` for the existing conversion contract.
The ideal target is `lround(calibrated_maximum * desired)`, limited to 0–100;
positive half ties round upward. Embedded float conversion remains owned by the
existing helper; vectors include half ties and scaling to guard operation order.
Do not round a fraction to integer schedule percent first or scale twice.
For two members capped at 100 and 60, a shared 75% demand gives 75 and 45.
Group manual remains relative; fixture manual is absolute, capped by its maximum.

Use current priority: absent/disabled fixture cannot transact; active invalid-time
safety supersedes manual; explicit scoped safe-off authorizes 0; fixture manual,
group manual, valid enabled automatic output, then hold. Group automatic-off
revokes automatic retries but does not send off. Existing scoped safe-off remains
requested while controls stay disabled; deliberate manual/automatic action may
supersede it unless live-clock safety is active. Keep the existing boot-uptime
invalid-clock grace (not a new time-since-failure grace) and fail-safe setting.
Invalid schedules block automatic requests without inventing a clock fault or
blocking independent manual controls. Invalid maximum rejects nonzero requests
but cannot prevent safety-off. ProT5 starts at zero maximum; commissioning is
required for nonzero UV. No editor action bypasses calibration or commissioning.

Schedule Apply/step-edge authorization cannot bypass BLE timing, bounded retries,
readback windows or stale-generation protections. Requested, pending, in-flight,
completed and reported values remain distinct; unknown/stale readback is never
physical confirmation. Other contexts and higher-priority fixture overrides
continue independently when one context is edited or invalid.

## 4. Acceptance corpus and T11 execution checklist

The checked-in [schedule cases](../tests/data/schedule-cases.json) are the
independent expected results. Their schema version describes the corpus, not
firmware persistence. Missing editor slots expand to disabled zero slots;
validation defaults and tagged NaN/infinity injection are described in its
`encoding` field. Numeric percentage tolerance is 0.0001 percentage points for
embedded float evaluation; final integer targets must match exactly. At a true
rounding boundary, test the established conversion operation order rather than
relaxing integer acceptance.

The corpus contains named schedules, direct timestamp/output expectations,
validation failures, exact fixture conversions, authorization transitions and
persistence/recovery scenarios. T11 must execute the scenario descriptions in
its policy/storage harness, not count JSON parsing as a behavioral pass.

- **AC1 — Model/validation:** execute `validations`, including enabled duplicates,
  malformed disabled fields, unused roles, capacity, sorting and all-zero output.
- **AC2 — Time/shape:** execute every `evaluations` entry with both providers;
  include cyclic wrap, exact midnight, fractional seconds, UV versus visible,
  leap-day equivalence and DST/correction snapshots. No event replay is allowed.
- **AC3 — Units:** execute `fixture_conversions`; two members of a shared group
  scale independently, UV zero stays zero, half ties match conversion, and
  fractional interpolation is not rounded early. For 09:00 minus 30 seconds in
  the visible rise, 49.583333% of a maximum 83 produces 41; rounding the schedule
  percent first would incorrectly produce 42.
- **AC4 — Editing/authorization:** execute `transitions`, proving atomic context
  rejection, dirty/Cancel behavior, Apply versus Unchanged, changed step bypass,
  unchanged retry budget, independent contexts and stale completion/readback.
- **AC5 — Control/capability:** preserve manual/calibration/safety/automatic-off
  priorities, autonomous HA-disconnected operation, simulation bench gating and
  live return. Schedule profiles omit T23 UI and seasonal private state.
- **AC6 — Durable state:** execute all `persistence_cases`, plus binary schema
  length/CRC/range/key-collision tests and torn-write injection. Reboot never
  enables automatic/manual output or restores staging/transactions.
- **AC7 — Profile/physical delivery:** both schedule profiles validate/compile
  with one engine/provider/orchestrator, no direct BLE path from the editor, and
  seasonal/T23 regressions still pass. T12/T15 add full matrix and physical traces;
  an Apply success is not physical lamp confirmation.

T10 completion means this behavior contract and independent expectations are
recorded. It does not mean schedule firmware exists, Gate A passed or this corpus
has passed against that future firmware. T11 must reference these IDs in its
results, implement missing negative/time-transition cases from the full contract,
and update the contract explicitly for any approved deviation. T15 supplies
actual schedule/storage/HA/ESP32-C3 observations before stable support is claimed.
