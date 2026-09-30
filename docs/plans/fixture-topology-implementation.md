# Unattended implementation runbook: T05R/T06R

Status: software implementation completed on `refactor/fixture-topology`;
hardware evidence and PR review remain open.
The owner subsequently requested the T05R/T06R refactor and a review PR.
[The architecture decision](fixture-topology-architecture.md) remains the
design input. No live controller was flashed during this work.

## Start conditions and source precedence

1. Inspect the working tree, repository instructions, remote default branch and
   PR #6. The reviewed baseline for this plan is T06 `e505851`, on top of T05
   merge `461783b`. If T06 is merged, start from the current default branch and
   inspect intervening changes. If still open, base the refactor on that branch
   and make any PR dependency explicit. Do not silently discard review changes.
2. Use a dedicated branch. Preserve unrelated work. Record the actual source SHA,
   ESPHome pin and resolved toolchain. Keep `requirements-ci.txt` at 2026.9.0 for
   this refactor unless an incompatibility is demonstrated and recorded as a
   separate change. Do not upgrade dependencies opportunistically.
3. Read the architecture decision, this runbook, `../baseline.md`,
   `../t05-extraction.md`, `../t06-control-policy.md`, `../architecture.md` and
   `../../todo.md`. For topology decisions this plan supersedes the old fixed
   mapping. Old behavior/evidence still governs compatibility where this plan
   does not explicitly change it.
4. Capture resolved local and remote-package configurations, generated entities,
   restore/preference identities, automations and target traces before changing
   firmware. Keep private settings and MACs outside Git. Public fixtures use
   obviously dummy values and are never deployment configurations.
5. Record progress in this file, one evidence entry per completed step. Make
   independently reviewable commits after each step passes its gate. Never mark
   a build or physical case passed merely because the architecture describes it.

## Current coupling to remove

| Current location | Verified coupling | Required result |
| --- | --- | --- |
| `packages/core/base.yaml` | Product-named MAC/enable substitutions | Generic topology descriptors plus an isolated legacy adapter |
| `packages/core/state.yaml` | Two-element fixture/engine arrays and shared state list | Separate fixture, group, context and controller state; explicit bounds |
| `packages/modes/seasonal.yaml` | One context; two array positions; fixture caps used for previews; calls policy directly | Role-labelled context output; preview conversion owned by fixture policy; orchestrator owns sequence |
| `packages/core/control.yaml` | `lamp > 1`, product-specific ternaries, two hard-coded queue actions | Group arbitration, routing and generic fixture policy; one authorization result |
| `packages/core/controls.yaml` | Product controls mix operational manual and test settings | Group/fixture operational controls separated from development inputs |
| `packages/core/dispatcher.yaml` | `due[2]`, two choices, product scripts, `1 - lamp`, engine evaluation tick | Enabled-slot round robin, static adapter dispatch, engine-free dispatcher |
| `packages/core/ble.yaml`, `packages/lamps/protocol.yaml` | Two fixed clients, duplicated frame/actions, callbacks writing shared state | Per-fixture adapters, one framing definition where feasible, correlated lifecycle events |
| `packages/features/diagnostics.yaml` | Fixed products and notification parsers mixed with diagnostics | Repeated fixture diagnostics, group delivery status, transport-owned parsing |
| `scripts/check_transport_scenarios.py` | Two-slot mock state and lambda extraction tied to product names | Production transition logic exercised for arbitrary identities, sparse slots and groups |
| CI/examples | Four enable combinations of one fixed pair | Topology matrix including repeated products, swapped roles and invalid configurations |

Audit these existing T06 risks while extracting; a passing build does not settle
them. Record failures and fixes as separate behavioral changes:

- `submit_control_target` checks authorization in a lambda and again in a later
  condition; use one explicit accepted/rejected result and captured source so an
  early return cannot leave a reusable stale target for later actions.
- Invalid-time request source is reconstructed from another clock read after
  calculation. Capture validity/source/revision once for that evaluation.
- Timeout calls failure handling, which clears `lamp_connected`, before testing
  whether to disconnect. Prove the old client/script is actually quiescent before
  another transaction starts; do not carry that ordering into generic adapters.
- Request generations handle pending replacement, but callbacks also need an
  active transaction identity so late events cannot release another transaction.
- A normal minimum-change threshold must not suppress a lowered fixture cap.
- Preview arithmetic and operational scaling currently have different float
  multiplication order. Preserve integer targets on the legacy regression corpus
  or document each intentional rounding change; do not assume algebraic equality
  guarantees identical embedded rounding.

## Ordered work packages

### R0 — Prove composition and freeze the topology syntax

**Depends on:** baseline capture. **No policy changes.**

Create the smallest reproducible local and remote-package fixtures proving two
instances of one reusable fixture fragment, then sparse slots and four instances.
Prove static include omission of a disabled fixture, unique IDs/controls, a single
radio/tracker and a single arbiter. Test both `esphome config` and generated C++
with the pinned version. A zero-MAC inactive client is not omission.

Select the concrete configuration syntax under the architecture's package-first
strategy. If required, implement the bounded schema/static-binding helper
described there, and prove that Device Builder's normal configuration path runs
its validation. No private external generator step. Record include variable names,
final validation order, local/remote path resolution and same-ref component loading.

**Gate:** an actual build rejects invalid references/roles/duplicate MACs and
accepts repeated product types, without runtime discovery or index semantics.
Commit the syntax decision, fixtures and proof. If this mechanism cannot work,
stop here with the exact failing case; do not build later steps on guessed syntax.

### R1 — T05R: isolate the composition and state owners

**Depends on:** R0. **Mechanical boundary work.**

Move the 10-second loop to a single orchestrator. Separate state ownership;
parameterise static fixture/client/entity IDs. Move readback parsing under the
transport boundary. Move repeated protocol definitions into shared templates or
helpers while preserving wire bytes, delay order, timeout/retry defaults and
notification semantics. Start with a topology adapter reproducing the legacy
visible/UV pair exactly. Do not rename public legacy entities as part of movement.

**Gate:** compare the resolved legacy inventories and expected wire traces with
the baseline, allowing only documented internal namespace/composition changes.
One orchestrator, one dispatcher and exactly one callback set per active fixture.
All globals have one owner. Full two-fixture compile and remote include pass.

### R2 — Add generic fixtures and the static topology validator

**Depends on:** R1. **Identity and routing descriptors, no group policy yet.**

Implement stable fixture IDs and explicit slots, the product catalogue, enabled
descriptor iteration, static client bindings and every validation rule in the
architecture. Disabled declarations produce no BLE/control artifacts. Generalise
transaction storage and round-robin selection, including nonadjacent slots.
Keep operating defaults from the legacy adapter.

**Gate:** single ProT5 in slot 0, single JungleDawn in slot 3, two JungleDawns,
two ProT5s and a reversed mixed pair all validate and route to the intended MAC.
Reordering declarations cannot change routing or persistence identity. No type
selection remains in shared code based on numeric slot. Full compile these
topologies; keep counts above two experimental.

### R3 — Context outputs and control groups

**Depends on:** R2. **Introduce independent policy state.**

Instantiate one or two selected-engine contexts; isolate every context's settings,
calculation state, validity and input snapshot. Publish role-labelled output
records containing desired/peak fractions, validity/reason, source and revision.
Route groups by explicit references. Group enable/manual state is independent
even when two groups consume the same context output. Build one group-to-members
fan-out; never rerun the engine for every physical member.

Use the legacy adapter to map both products to separate groups in one context.
Seasonal visible and UV formulas remain the existing formulas. Add no schedule
engine here. A shared context references one settings set; independent contexts
must remain isolated even when their initial values match.

**Gate:** shared two-visible-fixture group produces one logical decision and two
fixture requests; independent contexts change only their assigned outputs.
Two groups using the same logical output can have independent manual decisions.
No engine/context state contains a MAC, fixture cap, slot or transaction state.

### R4 — T06R: authorize and limit at the fixture boundary

**Depends on:** R3. **Behavioral policy work with explicit acceptance cases.**

Implement the architecture's source priority and controller/group/fixture scopes.
Use one captured decision through authorize → convert → enqueue, returning an
explicit outcome and reason. Store source/group/evaluation revisions on accepted
targets. Preserve fixture manual absolute-percent semantics; label the new group
manual fraction clearly. Calibrate each fixture separately. Do not fan out a
rounded/capped first member's target to other members.

Move preview conversion to the same routine as operational conversion. Enforce
invalid/non-finite rejection before casts. Queue off even with an invalid maximum.
Reevaluate cap reductions and policy revocations immediately. Preserve monotonic
retry/recovery behavior, per-fixture generations and in-flight sequencing.
Add transaction tokens and cleanup state where R0/R1 traces show they are needed.
Common dispatcher and transport receive final targets with identity/revision;
they cannot reinterpret seasonal state or manual priority.

**Gate:** pass the policy and transaction scenarios below against production logic
with a controllable fake transport. Fix each failing T06 audit case in a distinct
commit or clearly separated changeset with before/after evidence. A detached
simulation that merely reimplements expected logic is insufficient.

### R5 — Compatibility, entities and T07/T08 integration

**Depends on:** R4; complete alongside T07/T08.

Keep the legacy public entry path through an explicit compatibility composition;
add a distinct generic entry point and small real-format examples for the topology
matrix. Reject mixed old/new configuration except through that adapter. Preserve
legacy entities/settings where verified and publish a migration table where not.
Do not silently migrate or reuse calibration after physical assignment changes.

Add separate context, group and fixture diagnostics. Distinguish group demand
from per-fixture requested percent, write completion and physical readback.
Expose partial delivery and override exclusions. Remove test dependencies from
production through T07/T08; operational manual controls remain. Coordinate removal
of the simulation safety bypass as its own documented behavior change.

**Gate:** entity/preference inventories for legacy and new topologies are recorded;
production compiles without test IDs/providers; invalid topology fails in Device
Builder, local fixtures and remote imports. Reset/reassignment scenarios preserve
no stale calibration or pending commands. Physical persistence checks remain
explicitly blocked until hardware is available.

### R6 — CI matrix and release evidence

**Depends on:** R5; integrate the seasonal gate with T09 and later schedule coverage with T12.

Run the matrix below from the checked-out source, including exact production and
development entry points once T09 exists. Keep existing documentation-only CI
filtering behavior outside this refactor. Include schema failures, protocol
dispatch scenarios and firmware builds; pin the same toolchain as the baseline.
Record flash/static RAM deltas and physical minimum-heap measurements separately.
Validate a remote import at the proposed commit, not merely `master` or a prior tag.

**Gate:** software checks pass on the proposed commit; documentation identifies
which topologies are simulated/compiled versus observed on hardware. Publish no
four-fixture production-support claim until the hardware gate passes. Prepare a
reviewable PR and report remaining external evidence; do not merge, release or
flash unattended unless that separate action has been authorised.

## Required topology matrix

All valid rows require schema validation, resolved inventory checks and routing
scenarios. Full compile the listed topology variants; no need to enumerate every
slot permutation once explicit reorder/sparse-slot properties are covered.

| Case | Fixtures | Contexts / groups | Expected outcome |
| --- | --- | --- | --- |
| Legacy | JD slot 0, ProT5 slot 1 | One context, visible and UV groups | Legacy values/entities preserved or explicit migration |
| Visible only | JD slot 3 | One context, visible group | Sparse slot works; no UV fixture/client |
| UV only | ProT5 slot 0 | One context, UV group | UV calibration defaults to 0%; no visible fixture/client |
| Two visible shared | JD slots 0 and 1 | One context, one group | Single demand, independent caps and feedback |
| Two UV shared | ProT5 slots 1 and 3 | One context, one UV group | Separate 0% calibration defaults |
| Reversed mixed pair | ProT5 slot 0, JD slot 1 | One context, two groups | Role follows type/group, never index |
| Independent visible | Two JD | Two contexts, two groups | Changing one context leaves the other unchanged |
| Shared context, independent groups | Two JD | One context, two visible groups | Shared automatic calculation, independent manual/enable state |
| Four shared | Two JD and two ProT5 across two locations | One context, two groups | Two fan-outs; experimental until measured |
| Four independent | Two JD and two ProT5 across two locations | Two contexts, four groups | Independent vivarium policies; experimental until measured |
| Disabled/reserved | One enabled, other reserved slots | Only live group/context | No inactive MAC requirement, clients or ordinary entities |

Expected failures: five fixtures; slot 4; duplicate slot/ID/MAC; missing/zero/broadcast
MAC; unknown type/role/group/context; incompatible role/group; double membership;
unused group/context; zero enabled operational fixtures; mixed engine families;
unapproved >2-fixture production topology; duplicate/missing BLE bindings; mixed
legacy/new descriptors. Each failure must name the invalid configuration path
without printing private values. Disabled-only legacy builds are compatibility
cases, not proof of valid new operational topology.

## Behavioral acceptance cases

1. **Calibration fan-out:** shared demand 0.72, caps 100 and 60 → targets 72 and 43.
   Group manual uses the same fraction units. Fixture manual 80 with cap 60 → 60.
   One UV member's measured cap must never populate another's zero default.
2. **Override isolation:** manual fixture A leaves B automatic; releasing A uses
   the latest group revision. Group manual skips A while A has a local override;
   releasing group manual leaves A alone and reevaluates B.
3. **Safe-off scope:** group off affects only members, controller off affects all,
   fixture off holds that fixture at local 0%. A later explicit user request can
   replace explicit off; periodic hold cannot. Invalid-time safety still wins.
4. **Validation and limits:** NaN, infinity and out-of-range engine output cannot
   reach a wire byte. Invalid cap rejects nonzero but accepts safe-off. Reducing
   cap from 60 to 59 replaces pending 60 even with a 2% automatic threshold.
5. **Clock/source:** restored auto waits for valid clock; invalid-time grace and
   no-sync-expiry semantics match baseline. A clock change between evaluation and
   enqueue cannot change the request's source. Simulation cannot reach production
   routing; test the coordinated T07 safety change separately.
6. **Replacement:** in-flight 40, queued 60, newer 20 → complete 40 then send 20.
   Same numerical target with different source/revision still respects cancellation
   and cannot be mistaken for an old authorization.
7. **Cancellation:** cancel while connecting/writing/readback-waiting; late success,
   failure or disconnect must neither recreate pending work nor affect another
   fixture's transaction. Do not abort a protocol write midway to satisfy a test.
8. **Failure and reconnect:** A exhausts retries while B completes. A reconnects
   after the group's decision changes and sends only the latest authorised target.
   Test terminal failure, recovery backoff, timeout cleanup and monotonic wraparound.
9. **Partial delivery:** A confirms 0%, B is unavailable with a prior 70% report.
   Group is partial/unknown, B retains that report and fault; never display “all off”.
10. **Identity:** reorder declarations and use sparse slots without changing target
    destination, settings ownership or HA identity. New MAC/product at an old slot
    resets calibration/automation safely; label-only changes retain settings.
11. **Numerical compatibility:** representative seasons, leap/non-leap dates,
    dawn/noon/dusk/night, collapsed UV window, caps 0/1/59/60/100 and half-percent
    rounding boundaries. Compare legacy final targets, thresholds and frame traces;
    record tolerated floating diagnostics separately from integer target equality.
12. **Scheduling and bounds:** 1–4 enabled fixtures never overlap transactions;
    all eligible fixtures progress through round robin, with exact disabled-slot
    exclusion and per-fixture retry counts. Fairness is bounded after a failing
    transaction's timeout/cleanup, not dependent on its eventual success.

## Hardware gate and unattended stop rules

An unattended agent can finish software and simulation work and report external
evidence outstanding. It must not fabricate a bench pass or change a live vivarium.
Hardware evidence must identify board, firmware commit, lamp types/revisions,
topology, physical recovery method, minimum runtime heap, reconnect behavior,
watchdog stability and API/Wi-Fi responsiveness under unavailable-lamp and
four-fixture workloads. Keep the baseline application partition and record size
and headroom; no partition enlargement or higher connection allocation merely to
make a failing build pass. Gate A/T15 still apply.

Stop dependent work only for a concrete unmet prerequisite: unavailable required
baseline/review resolution, no valid pinned-version composition mechanism,
unexplained compatibility/rounding regression, unsupported hardware limit or
missing physical evidence required to advertise production support. Continue
independent documentation and software checks; report the exact missing evidence.

Deferred: runtime discovery/pairing, dynamic membership, more than four fixtures,
more than two independent contexts, mixed engine families, group physical-light
calibration, tightly simultaneous BLE delivery and automatic deployment/release.

## Completion record template

For each R step record: source/result SHA, changed boundaries, configuration syntax
or migration decisions, commands and results, topology cases exercised, entity/
persistence differences, numerical/protocol comparisons, build/resource evidence,
known limitations and next dependency. A later agent should be able to continue
from that record without interpreting this conversation.

- [x] R0 composition/validation proof (`fe69fa5`)
- [x] R1 T05R extraction into a separate generic package tree
- [x] R2 generic fixture identity/topology and static binding validation
- [x] R3 contexts/groups/routing with one seasonal evaluation per context
- [x] R4 T06R authorization, per-fixture caps and serialized transport
- [x] R5 legacy compatibility wrapper and generic entity/migration guide
- [x] R6 software CI matrix and release evidence in `docs/topology-controller.md`
- [ ] Physical hardware evidence required for advertised topology support

R1–R6 are delivered together because the operational package and its generated
bindings must compile as one unit. T07 now keeps development inputs out of both
production entry paths and provides a separate legacy development composition.
Local checks cover negative schema cases, nine topology compositions,
production C++ conversion/transport helpers, seasonal target parity, protocol
frames, safe-off scope and legacy configuration/firmware. The generic remote
Device Builder example is checked at this branch's pushed ref before PR review.
Physical BLE
timing, persistence after power cycle and four-fixture heap behavior remain for
bench testing before production support or a release claim.
