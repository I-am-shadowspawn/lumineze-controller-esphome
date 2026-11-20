# T10–T17 incremental delivery plan

Originally planned against `master` at `ab985a4` on 5 October 2026. Status
reviewed on **15 October 2026** against `implementation/t11-t17` at `73f9092`.
T10 and T11–T14 software deliveries now exist; this index distinguishes their
implementation evidence from outstanding physical acceptance. The
[integration handoff](../development-integration.md) records the review and
merge boundary for `implementation/t11-t17` -> `development`.

## Current evidence and start conditions

- T09 seasonal software build/parity/isolation evidence exists. Gate A's
  seasonal hardware smoke test and settings capture/restore remain open.
- T23 is merged through PR #14 (`038f78e` software hardening); its physical
  acceptance remains open. Use its [bench plan](t23-bench-validation.md).
- Four generic seasonal/schedule × production/development profiles and legacy
  compatibility wrappers are implemented and have recorded software evidence.
  Schedule profiles remain unverified candidates for device testing, not
  physically supported stable releases.
- CI pins ESPHome `2026.9.0`; observed ESP-IDF is `5.5.5` on ESP32-C3.
  Only that pin is qualified by the recorded software builds. Toolchain
  changes need a separate review and applicable regression/hardware reruns.
- `v1.9.0-rc` resolves to `fad8c4b`; `v1.0.0` remains the recovery/stable
  release tag. Neither proves the new `2.0.0-dev` candidate passed Gate B.
  Keep both tags immutable.
- The owner authorized isolated T11–T14 software work while Gate A remained
  open (5 October). Integration into development carries that authorization
  forward for device testing; hardware acceptance, release promotion and live
  deployment remain gated. No pending gate is closed by this merge.

## Plans and canonical task trackers

Each linked plan owns its incremental checkboxes. `todo.md` summarizes parent
tasks; software completion must not imply physical acceptance. Historical
execution records retain their original source SHAs and results.

| Task / implementation plan | Increment IDs | Current status / remaining exit |
| --- | --- | --- |
| [T10: schedule specification](t10-schedule-specification.md) | T10.1–T10.4 | Complete; contract and independent vectors included in the implementation branch |
| [T11: schedule engine](t11-schedule-engine.md) | T11.1–T11.6 | Software complete; [evidence](../evidence/t11-software.md); physical results remain Gate A/T23/T15 |
| [T12: profile CI](t12-profile-ci.md) | T12.1–T12.5 | Software complete, including 20 topology builds; current integration PR checks required before merge |
| [T13: release identity](t13-release-metadata.md) | T13.1–T13.5 | Software complete; T13.4 HA/device identity and update observations pending; parent remains open |
| [T14: user installation](t14-user-installation.md) | T14.1–T14.5 | Software complete; four pinned remote examples compile; physical commissioning remains T15 |
| [T15: hardware/compatibility](t15-hardware-compatibility.md) | T15.1–T15.6 | Protocol draft prepared; runtime budgets, bench measurements, migration and recovery pending |
| [T16: verified release](t16-verified-release.md) | T16.1–T16.5 | Planned; waits for accepted hardware evidence and frozen candidate |
| [T17: deployment proof](t17-deployment-proof.md) | T17.1–T17.6 | Planned; waits for verified release and authorized physical deployment |

## Dependency and readiness map

| Work | Available now | Remaining completion gate |
| --- | --- | --- |
| T10–T12 | Specification, implemented engines and software gates | Current full integration PR checks; no physical support claim |
| T13 | Shared identity, compatibility policy, metadata checks and release checklist | T13.4 runtime identity, retained settings and update observations |
| T14 | Minimal examples and installation/upgrade guides with remote build evidence | T15 physical commissioning; T16 final stable example refs |
| T15 | Draft [hardware protocol](../hardware-validation.md) and software baselines | Recorded Gate A results, frozen numeric runtime budgets and actual per-profile traces |
| T16 | Release checklist and candidate manifest | T15 acceptance at the final candidate; release publication authorized |
| T17 | Migration/second-controller plan | T16 verified release and authorized physical deployment |

Continue with T15.1 budget/protocol preparation and T13.4/T15 bench evidence.
If Gate A reveals a shared-code defect, fix it separately and rerun applicable
seasonal/T23/schedule regressions before accepting affected hardware results.

## Architectural changes delivered since the planning baseline

1. Context/role schedules route through explicit groups and fixture identities;
   physical slots have no product meaning.
2. The common orchestrator owns one input snapshot and tick. Seasonal settings
   are separate from shared context outputs; schedule builds omit seasonal
   private state.
3. Topology validation accepts the selected seasonal or schedule engine and
   rejects mismatched engine/context/editor/provider composition.
4. Seasonal temporary controls are composed separately from the common fixture
   path; schedule profiles do not expose T23. Shared authorization and stale-write
   revocation remain common.
5. CI covers the four profiles, legacy compatibility, both topology matrices,
   independent behavioral vectors, inventory isolation and immutable consumers.
   Documentation-only updates inherit successful source validation.
6. Compiled three/four-fixture support remains experimental. Physical support,
   runtime resource measurements, release and deployment require their own gates.

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

## Integration checkpoint — 15 October 2026

T10 and the incremental T11–T14 software commits are ready for review into
`development` as one integration PR, preserving their history with a merge
commit. No separate T10 merge is needed because its commits are ancestors of
`implementation/t11-t17`. Current software checks must pass before merging.

After integration, use development for controlled device testing, with private
wrappers pinned to the exact source SHA being tested. Gate A, T23, T13.4 and
T15 remain open; T16 release and T17 live deployment remain gated. Keep
`doc/ble-testing` independent, and leave `release`, `master` and published tags
unchanged. Resume from the first unchecked physical increment rather than
reimplementing completed software deliveries.
