# T10–T17 incremental delivery plan

Reviewed against `master` at `ab985a4` on 5 October 2026. This is documentation
work only; no firmware, workflow, settings, tag or device change is implemented
by these plans. Reinspect current master and instructions before implementation.

## Current evidence and start conditions

- T09 seasonal profiles have software build/parity/isolation evidence. Gate A's
  seasonal hardware smoke test and settings capture/restore remain open.
- T23 is merged through PR #14 (`038f78e` software hardening); its physical
  acceptance remains open. Use its [bench plan](t23-bench-validation.md) for
  traces; do not infer bench success from a PR merge.
- The repository currently has generic seasonal and legacy compatibility
  profiles. Schedule profiles are planned, not implemented or supported.
- CI pins ESPHome `2026.9.0` in `requirements-ci.txt`. The established board is
  the Pi Hut ESP32-C3 with ESP-IDF. Actual generated toolchain/partition versions
  must be recorded per implementation/build; do not change dependencies as part
  of this documentation delivery.
- The `v1.9.0-rc` tag currently resolves to `fad8c4b`. It does not close Gate A,
  T23, or Gate B. T13/T16 must inspect existing version history before choosing
  any next version; recovery tags remain immutable.

Documentation, independent expected vectors, compatibility inventories and bench
preparation can proceed now. The roadmap's Gate A still blocks schedule behavior
changes to shared firmware. T23 physical acceptance is not a new prerequisite
for writing T10–T17 plans or an automatic dependency for schedule mode; it is a
release gate for claiming that capability verified. T11 must retain its software
regressions and explicitly compose its seasonal-only capability.

## Plans and canonical task trackers

T10.1–T10.4 are complete as a specification delivery on `t10/schedule-specification`.
T11–T17 increments remain planned and unchecked. A checked parent in `todo.md`
requires its complete software and physical exit evidence, not just all code
committed. Each linked plan owns its incremental checkboxes; do not maintain a
second contradictory copy of those checkboxes in an issue or another file.

| Task / implementation plan | Increment IDs | Delivery / exit |
| --- | --- | --- |
| [T10: schedule specification](t10-schedule-specification.md) | T10.1–T10.4 | Settled behavior, editing/storage contract and independent expected vectors |
| [T11: schedule engine](t11-schedule-engine.md) | T11.1–T11.6 | Two schedule profiles, shared contract and seasonal/T23 regression evidence |
| [T12: profile CI](t12-profile-ci.md) | T12.1–T12.5 | Four-profile required builds, isolation, behavior and consumer gates |
| [T13: release identity](t13-release-metadata.md) | T13.1–T13.5 | Version/profile/toolchain correlation and compatibility policy |
| [T14: user installation](t14-user-installation.md) | T14.1–T14.5 | Minimal examples, commissioning/migration guides and clean remote builds |
| [T15: hardware/compatibility](t15-hardware-compatibility.md) | T15.1–T15.6 | Measured per-profile behavior/resources and demonstrated recovery |
| [T16: verified release](t16-verified-release.md) | T16.1–T16.5 | Immutable release with traceable evidence and verified pinned consumption |
| [T17: deployment proof](t17-deployment-proof.md) | T17.1–T17.6 | Existing-device upgrade and independent second-controller operation |

## Dependency and readiness map

| Work | Can prepare while physical testing proceeds | Implementation/completion gate |
| --- | --- | --- |
| T10 | Completed contract, edge-case tables and acceptance corpus | Review later T09/Gate A findings as amendments before T11 |
| T11 | Seam inventory, entity/persistence mapping and evaluator design | Gate A passed and T10 finalized before firmware edits |
| T12 | Coverage manifest, CI architecture and size/report design | T11 profiles exist and software acceptance passes |
| T13 | Namespace/version/compatibility decisions, release checklist | T12 evidence; runtime identity observations for completion |
| T14 | Example shape and user/migration journeys | T13 settled contract; actual candidate remote builds |
| T15 | Freeze bench protocol, budgets, recovery and trace format | T12–T14 accepted and Gate A evidence recorded |
| T16 | Release scope, notes and manifest template | T15 evidence on final candidate; publication authorized |
| T17 | Private backups, wrappers, rollout and second-device setup | T16 verified release; physical deployment authorized |

Default execution order remains T10→T11→T12→T13→T14→T15→T16→T17.
Preparation may overlap, but a blocked prerequisite is recorded explicitly and
cannot be bypassed by ticking a software-only task. If Gate A reveals a shared
policy defect, fix it separately and rerun applicable seasonal/T23 baselines
before schedule implementation begins.

## Review findings that the plans resolve

1. Original T10/T11 language refers to two lamp targets. The new plans define
   independent context/role schedules routed through groups to fixtures; slot
   numbers have no product or role meaning.
2. `packages/topology/controller-core.yaml` includes the seasonal engine.
   `seasonal-engine.yaml` owns the orchestrator/interval, while `ContextState`
   mixes seasonal settings and shared outputs. T11.1 separates these mechanically
   before schedule behavior; schedule builds must omit seasonal private state.
3. `lumineze_topology` validation allows only seasonal engine family today.
   T11.4 must validate the selected engine/context fragments, not just permit a
   new string while retaining a seasonal-only composition.
4. T23 controls live in `fixture-luminize.yaml`, and its software transitions
   rely on shared authorization helpers. T11.5 makes UI/capability composition
   explicit without weakening common stale-request protections or extending
   seasonal-only behavior accidentally.
5. Current CI covers seasonal generic and legacy fixtures. T12 adds actual
   schedule builds, manifest-based inventory checks and independent vectors,
   retaining doc-only skip behavior and bounded download retries.
6. Compiled topology support is broader than physical evidence. T15 keeps
   experimental three/four-fixture results separate and sets budgets before
   candidate measurements. T16/T17 require release and real-install evidence.

## Increment execution record

Append a record under the relevant plan when an increment starts/completes:

```text
Increment: Txx.n
Status: planned | in progress | blocked | complete
Source SHA / branch / toolchain:
Owner: implementation agent or developer; hardware operator for physical steps
Changed artifacts / commit / PR:
Acceptance criteria exercised / commands / results / evidence:
Persistence, HA identity and rollback impact:
Dependencies/blockers and remaining physical checks:
Deviations from the plan and reason:
```

Commit each independently reviewable increment after its acceptance checks.
An issue can refer to these IDs, but must link back to the canonical progress
record. For hardware work, record actual operator/time/configuration and raw
trace locations; keep device secrets and MACs private. Mark a parent task complete
only when every required increment and exit condition has evidence. A gate cannot
be closed by an expected result, successful compilation or a plan document.

## Completion boundary of this planning delivery

Eight implementation plans and their incremental trackers are documented and
linked from the roadmap. T10 specification work is complete; actual T11–T17
implementation remains unstarted. No live controller
is flashed, no release is promoted, and no hardware gate is marked complete.

## Active implementation checkpoint — 5 October 2026

Owner authorized T11–T14 isolated software work while hardware gates remain open.
Branch: `implementation/t11-t17`, based on completed T10 `c250604` (development
contains the planning baseline). T11.1 extraction and T11.2 pure evaluator are complete with evidence in the T11
plan. T11.3a storage core is verified; next: T11.3b HA editor/lifecycle integration. T11 is not yet complete;
Gate A, T23 physical acceptance, release and deployment gates are still open.
Commit each increment and update its canonical plan before proceeding. If usage
ends, resume the first unchecked T11 increment; do not restart the extraction.
