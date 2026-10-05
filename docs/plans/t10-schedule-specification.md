# T10 — Specify the daily schedule contract

**Entry:** documentation and test-vector design can proceed while Gate A is
pending. Finalize the contract after reviewing T09 hardware findings; no
schedule firmware changes before Gate A passes.
**Dependencies:** T09/Gate A. **Delivery:** an unambiguous specification and
independent expected results for T11; no firmware implementation.

## Recommended bounded design for the specification

These are proposed decisions for T10 to settle and record, not existing product
capabilities. Use the generic topology: up to two contexts, each with independent
`visible` and `uv` schedules, routed through up to four groups/fixtures. Product
and physical slot do not select a schedule. Groups can share one context/role.

Start with eight fixed point slots per role/context. A point has enabled state,
local minute-of-day (integer 0–1439), and level (integer 0–100, **percent of each
fixture's calibrated maximum**). Support a role-wide step or linear mode. Used
roles need at least two enabled points; disabled slots have no output effect.
Reject duplicate enabled times, invalid/non-finite settings and malformed data.
Sort validated points on Apply; staged storage order does not define playback.
An unused role may have no active points. An all-zero two-point schedule is valid.

Treat schedules as cyclic local days: the final point connects to the first
through midnight. Step holds the previous point; linear interpolates that cyclic
segment, including wrap. Exact point time yields that point's level. Users add
explicit zero points for an off overnight period. There is no implicit sunrise,
seasonal maximum, weekly calendar or runtime engine switching.

Stage edits in HA and Apply the complete context snapshot atomically. Invalid
Apply leaves active settings/output intact. Cancel Edits restores staging from
active settings. Persist only complete validated active snapshots using a
versioned integrity-checked format; staging and temporary actions do not restore.
New/invalid restored schedules have invalid automatic output, automatic groups
remain off at boot, and commissioning requires an explicit Apply. Define safe
initial staging defaults without silently activating them.

Use the shared local wall-clock snapshot, not timed-event replay. Spring skipped
times evaluate the current segment at the new time; repeated autumn times replay
the applicable segment, with no once-only event latch. Startup and clock
correction evaluate now; missed points are not replayed. Invalid live clock uses
the existing grace/safety policy. Dispatcher/retry timers remain monotonic.

Automatic levels obey ordinary fixture thresholds. Specify step boundaries and
successful Apply as explicit reevaluation events that bypass minimum-change when
the final target changes; identical accepted targets do not reset retry budgets.
Linear intermediate changes use the normal filter. A generic transition revision
may express that intent in T11; it must not turn every evaluation into a request.
Temporary T23 controls retain their documented seasonal-only scope.

## Incremental deliveries

- [x] **T10.1 — Audit and decision record.** Inspect snapshot, output conversion,
  groups, preferences and existing HA entities. Record the choices above and
  alternatives in `docs/schedule-behaviour.md`, including capacity, units,
  interpolation, minimum-change and used/unused role rules. Map every existing
  T10 roadmap edge case to a section. Acceptance: no product-slot assumptions
  and no unresolved normal-output rule.
- [x] **T10.2 — Time and boundary specification.** Add before/at/between/after
  and midnight tables for step and linear schedules; specify seconds as a
  fraction of a minute, leap-day independence, DST, forward/backward corrections,
  invalid clock, disabled slots, missing points and startup. Acceptance: expected
  results are determinable from timestamp plus active snapshot alone.
- [ ] **T10.3 — Editing, persistence and control contract.** Specify staged
  entity IDs, atomic context Apply/Cancel, rejection messages, active revision,
  boot defaults, schema corruption handling and upgrade/rollback. Document
  fraction output, calibration once, manual/off/safety priority, and independent
  group effects. Acceptance: a failed edit never changes active output or
  persistence; a successful edit has an explicit application boundary.
- [ ] **T10.4 — Independent golden cases and handoff.** Store hand-worked input
  and expected fractional/final-target vectors (proposed
  `tests/data/schedule-cases.json`) and explain calculations. Include 08:00=0,
  10:00=100, 18:00=100, 20:00=0: linear 09:00=50, step 09:00=0, midnight=0;
  wrap 22:00=40/02:00=0 gives linear midnight=20. A 75% demand with a 60%
  calibrated fixture gives 45%. Add rejection and step 50→51 with threshold 2.
  Acceptance: each case has an independently recorded expectation and T11 can
  implement without inventing behavior. Link the finalized spec from README/todo.

## Exit and scope control

T10 is complete when all four records are reviewed against the roadmap and Gate A
findings. Keep specification changes separate from engine code. Revision of a
settled output rule requires updated vectors and an explicit compatibility note.
Weekly calendars, dynamic topology and T23 schedule support are follow-up scope.

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

## Execution record

### T10.1 — complete

Source: development `e786bee`; branch `t10/schedule-specification`; CI pin
ESPHome 2026.9.0. Audited generic schema/state, orchestrator, conversion,
arbitration, preferences and T23 seams. [Contract section 1](../schedule-behaviour.md)
settles capacity, units, topology, validation and alternatives, with explicit
entity/storage estimates. Verification: matched owner paths to the checkout,
reviewed roadmap T10 decisions and ran `git diff --check`. No firmware change;
Gate A remains pending and gates T11.

### T10.2 — complete

[Contract section 2](../schedule-behaviour.md) specifies cyclic point evaluation,
separate visible/UV tables, fractional minutes, wrap, disabled/out-of-order
points, DST/corrections, startup, invalid clocks and transition filtering.
Verification: manually checked 09:00=50, UV 09:30=40, wrap midnight=20 and
fractional-minute expectations against their documented segments; `git diff
--check` passes. No time events are replayed and no firmware changed.
