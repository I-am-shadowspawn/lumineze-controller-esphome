# Development integration and device-test handoff

Reviewed **15 October 2026**. Source baseline: `implementation/t11-t17` at
`73f9092d80d7c3918ab2d622c3bac2964f8c523a`; target baseline: `development` at
`e786bee41f61b7b9f7c0d149653b0ac7fdf4e9f3`.

## Scope and review outcome

The implementation is 30 commits ahead of development with no divergence.
Its ancestry already contains all four T10 specification commits; no separate
T10 merge is needed. Integrate using a **merge commit**, retaining the original
incremental commits and their evidence. Documentation corrections in this
integration do not change firmware, toolchain, version or release status.

The combined review covers engine composition and schema ownership, cyclic
schedule evaluation, staged Apply/Cancel and two-bank storage, role transition
authorization and obsolete-write revocation, seasonal/T23 isolation, build
identity, CI gates and pinned consumers. The current host regressions and PR
builds are required in addition to the earlier source-specific evidence. None
of these checks establish real BLE delivery or durable settings on hardware.

| Delivery | Integration content | Evidence / remaining boundary |
| --- | --- | --- |
| T10 | Schedule contract and independent acceptance corpus | [Specification](schedule-behaviour.md) and [plan](plans/t10-schedule-specification.md) |
| T11 | Schedule profiles, editor/storage and common control integration | [Software acceptance](evidence/t11-software.md); physical behavior remains pending |
| T12 | Four-profile CI, both topology matrices, fault/isolation gates and consumers | [CI checks](ci-validation.md); current PR must pass |
| T13 | Identity, compatibility policy and unreleased `2.0.0-dev` metadata | [Software evidence](evidence/t13-software.md); T13.4 HA/device/update observations pending |
| T14 | Four pinned wrappers, installation and recovery instructions | [Remote build rehearsal](evidence/t14-installation.md); no physical commissioning claim |
| T15 | Draft bench protocol and resource limits | [Hardware validation](hardware-validation.md); numeric runtime budgets and all physical acceptance pending |
| T16–T17 | Release and deployment plans | Planned, not performed by this integration |

## Verification and merge gate

Before raising the PR, reconcile the delivery index, task-plan introductions,
roadmap and installation entry points with the completed software records.
Historical evidence keeps its original SHA: an older successful build does not
become a build of the new documentation commit.

Local review runs use the pinned ESPHome 2026.9.0 environment:

- `scripts/check_fast_gates.py`: declared C++/behavioral regressions, including
  schedule numeric, storage, editor, policy and seasonal/T23 regressions.
- Fault checks: `check_gate_faults.py`, `check_build_resilience.py`,
  `check_ci_change_scope.py`, `check_release_metadata_faults.py`.
- Schema/composition: `check_topology_schema.py`, `check_schedule_schema.py`,
  both `check_topology_matrix.py` configuration matrices and input isolation.
- Identity/compatibility: `check_release_metadata.py`,
  `check_project_metadata.py`, `check_update_identity.py`,
  `check_seasonal_inventory.py`.
- Documentation links, current status consistency and `git diff --check`.

Local review on 15 October passed every command group above on the unchanged
firmware source. The fast runner reported all declared software gates passing;
the schema/identity/fault and both configuration-matrix runs also completed
successfully. Full firmware compilation is delegated to the current GitHub
checks; no on-device result is claimed.

GitHub must run **full software validation on the integration PR**: four
profile builds, validate/legacy/topology regressions, immutable consumer and
**Required validation**. Check the PR's current head and merge revision, not
only historical runs or a documentation-only skip. Merge only after these
checks succeed; failures must be resolved or leave the PR unmerged.

The latest historical branch run failed while querying GitHub check metadata
with HTTP 500, not a demonstrated firmware defect. A full pre-integration
revalidation was requested at source `73f9092`:
[run 38717256387](https://github.com/I-am-shadowspawn/lumineze-controller-esphome/actions/runs/38717256387).
Its eventual result is separate from the current PR's acceptance. The PR's
Checks tab records current execution; this document does not predeclare success.
No repository protection settings are changed by this integration.

## Development after merge

Development becomes the integration source for controlled device testing.
Choose its **exact full source SHA**, record the selected profile and use that
same SHA for the Git package and external component in a private wrapper.
The public examples retain their earlier build-tested `controller_ref`; replace
that value deliberately when testing newer development. Never treat the moving
branch name or the word `production` in a profile as hardware acceptance.

Record board/lamp identities, topology, toolchain/partition, calibration,
firmware SHA, expected and observed output, timestamps and recovery results
using the [hardware protocol](hardware-validation.md). Have an operator perform
and record the physical steps. Before changing an existing installation, retain
its known-good firmware, private configuration/settings and serial recovery path.

| Open gate | Evidence still needed |
| --- | --- |
| Gate A / T09 | Seasonal hardware smoke/parity and settings capture/restore |
| T23 | Daily maximum and timed-fixed physical sequences with requested/completed/reported BLE traces |
| T13.4 | Actual HA/device identity, disabled boot/update controls and retained-state observations |
| T15 | Frozen runtime resource budgets, per-profile behavior/fault/soak/OTA tests and migration/recovery evidence |
| T16 | Accepted candidate, immutable release identity and publication |
| T17 | Verified-release upgrade and independent second-controller operation |

The later app-driven BLE research stays on `doc/ble-testing`; it is not merged
or substituted for ESPHome acceptance. `release`, `master` and published tags
remain unchanged. Successful software checks authorize integration into
development, not release promotion, live deployment or a device flash.
