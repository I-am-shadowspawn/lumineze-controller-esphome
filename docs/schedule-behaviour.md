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
