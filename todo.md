# LuminEZE implementation roadmap

Prepared: 29 September 2026  
Status: implementation underway. T01–T08 have source/build evidence; live hardware and settings observations remain for Gate A. T05R/T06R have a generic static-topology implementation and software matrix; physical multi-fixture evidence remains outstanding.

Planning update, 30 September 2026: the [fixture/group architecture](docs/plans/fixture-topology-architecture.md)
and [unattended implementation runbook](docs/plans/fixture-topology-implementation.md)
supersede fixed two-lamp topology assumptions in this roadmap. R0–R4 are
complete; coordinate R5 across T07/T08 and the seasonal R6 gate with T09. Keep
original T05/T06 completion evidence intact.

## Purpose and starting point

Turn the existing ESPHome vivarium controller into a reusable, modular project with four supported firmware profiles:

| Profile | Control engine included | Development test controls | Operational diagnostics |
| --- | --- | --- | --- |
| `seasonal-production` | Seasonal simulation | Excluded | Included |
| `seasonal-development` | Seasonal simulation | Included | Included, with additional detail |
| `schedule-production` | Configurable daily schedule | Excluded | Included |
| `schedule-development` | Configurable daily schedule | Included | Included, with additional detail |

**Build time selects capabilities; runtime configures the selected capability.** Changing the engine or adding test facilities requires a new build. Changing normal operating parameters should not.

This roadmap is based on the supplied design discussion. The original controller YAML, repository, firmware and hardware measurements were not available when it was written. Descriptions of the current implementation are therefore assumptions to verify in T01, not a completed code review. Existing identifiers mentioned in the discussion, including `calculate_solar` and `solar_test_mode`, are investigation leads rather than requirements to rename anything.

The recorded baseline is an ESP32-C3 using ESP-IDF with JungleDawn at index 0 and ProT5 at index 1. Preserve it as a compatibility fixture. The planned architecture gives physical slots no product/role meaning and introduces contexts, groups and explicit routing, initially bounded at four fixtures with hardware support gated separately.

## Intended boundaries

| Concern | Intended responsibility |
| --- | --- |
| Local device YAML | Device identity, chosen profile, timezone, explicit fixture/group/context topology, per-fixture MACs/location labels, and local credentials |
| Shared platform configuration | Board/framework, common networking behaviour, logger, API and OTA support |
| Clock and evaluation input | Supply a coherent date/time/validity snapshot to the selected engine |
| Selected engine | Calculate role-labelled logical outputs per context; contain only that mode's settings and calculations |
| Control groups and routing | Share or isolate control decisions and route them to explicit fixture members |
| Control policy | Resolve automatic/manual requests, limits, commissioning state and invalid-input behaviour |
| Dispatcher and BLE transport | Queueing, ordering, retry, timeout, reconnection, writes, notifications and readback |
| Production diagnostics | Explain controller health and what is requested versus actually confirmed |
| Development features | Simulated inputs, deliberate transport exercises and additional diagnostics |
| Profile | Compose one supported combination of the above |
| Bootstrap/adoption | Provision and identify a new controller before normal operation is commissioned |

The intended data flow is: evaluation snapshot → engine context → logical output → group decision → fixture routing → fixture policy/limits → dispatcher → BLE fixture. Lamp readback feeds diagnostics and transaction state; it must not be confused with the requested output.

Runtime settings should include the selected mode's times/levels or seasonal parameters, calibration and maximum brightness, automatic control and supported manual override. Review existing retry settings: retain runtime controls where useful and safely bounded, without exposing every protocol constant as a user setting.

Production must remain independent of development packages. Hiding a test entity in Home Assistant, setting a test switch to false, or marking an entity internal is not proof that its functionality was omitted from firmware.

## Working method

1. Start each task by reading its dependencies and recording a short implementation plan. Resolve that task's open decisions at that point; do not require every future decision before starting T01.
2. Identify actual files, IDs, persisted values and behaviour before editing. Treat the proposed paths below as a starting layout, not a requirement to create empty modules.
3. Keep mechanical movement, changes to behaviour, and new capabilities in separate reviewable changes. A newly discovered bug gets its own documented change and evidence.
4. Validate and compile affected profiles after each meaningful change. Introduce automated checks early and expand them as profiles become real.
5. Record evidence against acceptance criteria. Compilation, behavioural checks and hardware checks prove different things; a compile pass alone does not make a profile production stable.
6. Update this file as work proceeds. Mark a task complete only when its acceptance criteria and the relevant evidence are recorded. Record blocked hardware checks explicitly.

Suggested planning record for each task, stored in the task notes or linked issue:

```markdown
Task ID:
Source commit and ESPHome/toolchain version:
Observed current behaviour and affected files/IDs:
Decisions, alternatives considered, and rationale:
Implementation steps and scope exclusions:
Validation cases and expected results:
Configuration/persistence migration and rollback impact:
Completion evidence, remaining limitations, and follow-up tasks:
```

## Execution checklist and milestones

Work in the listed order by default. Dependencies identify prerequisites, not permission to skip the milestone gates.

### A — Establish a modular seasonal controller

- [x] T01 — Capture the current working baseline and recovery information. Owner-reported deployed YAML, `v1.0.0` recovery source, local build and remaining field-evidence gaps: `docs/baseline.md`.
- [x] T02 — Establish the repository, private configuration boundary and build environment. Evidence: `docs/build.md`, `requirements-ci.txt`, clean local fixture build.
- [x] T03 — Define module ownership and the common control contract. Evidence: `docs/architecture.md`, including every explicit ID.
- [x] T04 — Create a reusable package and the first automated build fixture. Evidence: local full compile and passing push/PR builds in `docs/build.md`.
- [x] T05 — Split the implementation into functional modules without changing behaviour. Evidence: `docs/t05-extraction.md`, identical pre/post resolved fixtures, remote package import and full local/CI builds.
- [x] T06 — Separate control policy from the selected algorithm and BLE transport. Evidence: `docs/t06-control-policy.md`, simulated transport transitions, all four configuration fixtures and a two-light firmware build.
- [x] T05R — Rework topology/composition and generic fixture ownership (R0–R2 in the [runbook](docs/plans/fixture-topology-implementation.md)); retain the legacy pair as a regression case. Software implementation and compile matrix are in the fixture-topology refactor PR; hardware support remains gated.
- [x] T06R — Introduce context outputs, control groups, fixture routing and generic authorization/dispatch (R3–R4 in the runbook). Software implementation and policy/transport tests are in the fixture-topology refactor PR; R5–R6 and physical evidence continue with T07–T09.
- [x] T07 — Isolate simulated inputs and development test controls. Production and development snapshot providers are separate; development simulation and bench-output controls reset off, and seasonal code consumes only the captured snapshot.
- [x] T08 — Separate operational diagnostics from verbose development diagnostics. PR #11 passed both CI validation runs; see [diagnostic profile inventories](docs/diagnostic-profiles.md).
- [ ] T09 — Assemble and verify both seasonal profiles. PR #13's remote CI passed both seasonal ESP32-C3 profile builds, provider-isolation and snapshot-parity checks; the physical seasonal bench smoke test and settings capture/restore remain outstanding for Gate A.

**Gate A:** the modular seasonal build matches the recorded baseline, and seasonal production builds with all development test facilities omitted. Do not add schedule behaviour to shared code before this boundary is demonstrated.

### Independent feature after Gate A

- [ ] T23 — Add a temporary daily automatic maximum and timed fixed level per fixture. Begin after T09; this does not depend on the schedule or adoption tasks. See the [requirements](docs/temporary-lighting-requirements.md) and [implementation plan](docs/plans/temporary-lighting-implementation.md).

### B — Add schedule mode and establish a stable release

- [ ] T10 — Specify configurable schedule behaviour and edge cases.
- [ ] T11 — Implement schedule mode behind the same control contract.
- [ ] T12 — Enforce the four-profile build and regression matrix.
- [ ] T13 — Add project identity, compatibility policy and release metadata.
- [ ] T14 — Create minimal device examples and installation documentation.
- [ ] T15 — Validate hardware behaviour, resource headroom and upgrade compatibility.
- [ ] T16 — Publish the first verified modular release.
- [ ] T17 — Migrate the existing controller and provision a second controller.

**Gate B:** all four advertised profiles pass their defined checks, the existing installation has a verified upgrade/recovery path, and another controller can be configured without copying controller logic. Seasonal-only release is possible if schedule is deferred explicitly; do not label incomplete schedule profiles supported.

### C — Add generic provisioning and Device Builder adoption

- [ ] T18 — Design bootstrap, adoption and commissioning as distinct states.
- [ ] T19 — Implement and test generic provisioning firmware.
- [ ] T20 — Implement dashboard adoption and explicit lamp commissioning.
- [ ] T21 — Extend CI and release checks to bootstrap and adoption artifacts.
- [ ] T22 — Rehearse a fresh installation and release the adoption workflow.

**Gate C:** a fresh controller can be provisioned, adopted, paired by explicitly supplied MAC addresses and installed as a chosen production profile using only the published instructions. Its uncommissioned state cannot issue operational lamp commands.

## Proposed repository layout

Use meaningful ownership boundaries. Merge small, tightly coupled files when that is clearer. The T05R/T06R plan's module ownership table supersedes topology-specific rows in this original layout; retain the remaining profile/release boundaries.

| Path | Intended contents |
| --- | --- |
| `packages/core/base.yaml` | Shared platform/network defaults; no installation credentials |
| `packages/core/time.yaml` | Real clock sources, validity and timezone handling |
| `packages/core/control.yaml` | Mode-independent evaluation orchestration and request arbitration |
| `packages/core/ble.yaml` | Shared BLE/tracker setup; static per-fixture adapters move under the planned transport boundary |
| `packages/core/dispatcher.yaml` | Transaction state, queueing, retries and readback processing |
| `packages/core/safety.yaml` | Common limits and fault policy; may initially live in `control.yaml` |
| `packages/lamps/` | Lamp-specific protocol details and common user-facing lamp controls |
| `packages/modes/seasonal.yaml` | Seasonal calculations, configuration and mode-specific status |
| `packages/modes/schedule.yaml` | Daily schedule calculations, configuration and mode-specific status |
| `packages/inputs/` | Mutually exclusive live versus development evaluation-input providers, if needed |
| `packages/features/diagnostics.yaml` | Common production health information |
| `packages/features/test-*.yaml` | Development-only simulation/transport exercises |
| `packages/features/verbose-diagnostics.yaml` | Additional development reporting |
| `packages/profiles/` | Four public profile entry points; optional internal shared compositions |
| `examples/` | Minimal device configurations and placeholder-only secret examples |
| `tests/configs/` | Standalone local-package build fixtures for CI |
| `tests/` | Behavioural fixtures, profile-content checks and expected outputs |
| `docs/` | Architecture, operating behaviour, installation and regression evidence |
| `adopt/` | Public adoption entry point or entry points, introduced in Phase C |
| `firmware/` | Bootstrap build entry point, introduced in Phase C |
| `.github/workflows/` | Validation, compile matrix and release checks |
| `README.md`, `CHANGELOG.md`, `LICENSE` | Project entry point, release history and chosen licence |

Do not commit private live-device YAML or raw backups merely to fit this layout. Keep the exact deployed baseline privately; only a reviewed, sanitised reference belongs in a shareable repository.

## Task details

### T01 — Capture the current working baseline and recovery information

**Depends on:** nothing.  
**Intent:** establish what must remain unchanged before restructuring it.

**Planning must settle:** which YAML and firmware are actually deployed; whether outstanding local edits exist; exact board/flash variant; current ESPHome and framework versions; availability of a spare controller and recovery connection.

**Work:**

- Obtain the current YAML and its included files. Preserve an exact private backup, required credentials, current runtime settings and an available recovery firmware/build path.
- Inventory IDs, entity names, device identity, restored globals/numbers/switches, boot actions, time sources, timers, BLE transaction state and automatic/manual behaviour.
- Confirm the two-lamp mapping and record the commands, acknowledgement/readback semantics and known failure behaviour.
- Capture representative seasonal inputs and outputs, including night, dawn, midday, dusk, winter/summer extremes, year boundaries and leap day. Record current invalid-clock behaviour.
- Record current build size and any available heap/uptime/connection observations. Separate measured facts from assumptions and known defects.

**Done when:** a baseline record identifies the source/build/settings and recovery method; later work has concrete behaviour to compare against; missing evidence is listed explicitly. No private baseline or credential-bearing compiled firmware is published.

### T02 — Establish the repository, private configuration boundary and build environment

**Depends on:** T01.  
**Intent:** make changes traceable and builds repeatable before changing architecture.

**Planning must settle:** repository owner/name/visibility, licence choice, supported build environment, and whether the existing toolchain can support the proposed package composition. Do not pick an arbitrary minimum version from the earlier examples.

**Work:**

- Create or prepare the repository and add this roadmap. Add ignore rules for `secrets.yaml`, private device configurations, generated build output, caches, private logs and firmware artifacts.
- Add a sanitised baseline reference only after reviewing both literals and referenced files for private information. Record how it differs from the exact private backup.
- Pin a reproducible ESPHome build environment and record the resolved framework/toolchain. Initially retain the working version where feasible.
- If a toolchain upgrade is necessary, validate it as a separate baseline change before mixing it with the refactor.
- Establish a clean-checkout build procedure and the naming convention for fixture devices and temporary settings.

**Done when:** a clean checkout can reproduce the baseline validation/build using documented private inputs or a sanitised fixture, without exposing real credentials. Any toolchain-related behaviour change is independently accounted for.

### T03 — Define module ownership and the common control contract

**Depends on:** T01–T02.  
**Intent:** ensure files are separated by responsibility and both engines use one output path.

**Planning must settle:** the concrete ESPHome mechanism for the interface—parameterised scripts, explicitly owned globals, or small shared C++ helpers—and exact units, state ownership and invocation order. Prefer the smallest solution compatible with the existing code.

**Work:**

- Map every existing section/ID to one owning module; document cross-module references and shared state. Identify where algorithm code currently touches BLE or test entities.
- Define one evaluation snapshot: date/year information, local time, validity and any required source information. Keep transaction timeouts based on a monotonic real clock, independent of simulated dates/times.
- Define engine output for both lamps: desired level, validity and, if useful, a reason. Specify scale, rounding, non-finite input handling and where lamp maximum/calibration is applied exactly once.
- Define the priority of common constraints, automatic requests and manual requests. Specify behaviour when requests change during a pending transaction.
- Define requested, queued/sent and confirmed/reported values separately, with freshness where needed. Decide which shared orchestrator triggers evaluation.
- Record exactly one owner for each timer, boot hook, transaction state and persisted setting. Define which common controls remain in production.

**Done when:** `docs/architecture.md` contains an ownership map and an implementable contract. Seasonal and schedule engines can meet it without knowledge of BLE client IDs or queue internals. Open policy choices are assigned to a later named task.

### T04 — Create a reusable package and the first automated build fixture

**Depends on:** T02–T03.  
**Intent:** prove the local/private configuration boundary before moving many sections.

**Planning must settle:** substitution names and defaults, which inputs are mandatory for a normal controller, and the smallest representative fixture. A temporary single-package intermediate is acceptable; it is a checkpoint, not the final architecture.

**Work:**

- Parameterise device name, friendly name, area, timezone and the two lamp MAC addresses. Preserve the existing installation's identity, including any existing spelling, unless a separate migration is intended.
- Keep Wi-Fi, API encryption and any OTA credentials in the local device configuration. Shared packages must not depend on private secret lookups.
- Create a local-package fixture using non-operational MAC placeholders and syntactically valid dummy credentials where required. Clearly identify fixtures as build inputs, not installable production configurations.
- Validate and compile the fixture. Compare merged configuration and generated behaviour with the baseline, allowing only documented identity/credential differences.
- Add initial CI for that fixture, building the checked-out source. Do not have PR checks fetch an old released package instead of the change under test.

**Done when:** a small device YAML supplies installation data and includes the shared implementation; the first fixture passes locally and in CI; no controller logic has been duplicated into the device YAML.

### T05 — Split the implementation into functional modules without changing behaviour

**Depends on:** T04.  
**Intent:** make the implementation navigable while retaining a reliable comparison point.

**Planning must settle:** actual extraction order from the ownership map, strongly coupled sections best moved together, and how to preserve existing cross-references during intermediate commits.

**Work:**

- Extract platform/time, BLE, dispatcher, lamp controls/protocol details, seasonal calculations and diagnostics in manageable changes. Keep existing test behaviour temporarily where necessary until T07.
- Preserve IDs, entity names, restore settings, defaults, timing, ordering and numerical expressions during these moves.
- Review merged automations for duplicated boot hooks, intervals and callbacks. Check actual resolved configuration rather than assuming an include replaces an earlier definition.
- Validate and compile after each meaningful extraction; rerun affected baseline cases.
- Document each module's purpose, owned IDs, inputs and outputs. Remove the temporary monolith once nothing depends on it, retaining the reference/history.

**Done when:** the controller builds from functional modules and passes the agreed baseline comparisons. Mechanical movement has not silently become an algorithm or default-setting change.

### T06 — Separate control policy from the selected algorithm and BLE transport

**Depends on:** T05 and the T03 contract.  
**Intent:** provide one consistent path from desired output to lamp communication.

**Planning must settle:** boot behaviour, invalid/stale time, invalid engine output, automatic-disable semantics, manual-override duration, limits and reconnect behaviour. Preserve baseline policy unless a change is explicitly recorded with its own acceptance cases.

**Work:**

- Route seasonal and manual requests through the common arbitration/limit path. Keep automatic enable/disable and intended operational manual controls available in production.
- Remove algorithm-specific conditions from the dispatcher. Keep wire encoding, retries, readback and connection handling below the common contract.
- Ensure stale pending requests cannot unexpectedly win over a newer decision. Define coalescing/replacement and safe cancellation rules without bypassing transaction sequencing.
- Make limit, invalid-time and communication-fault behaviour observable. Specify what happens when one lamp is unavailable while the other remains connected.
- Document that a request to turn a disconnected lamp off is not confirmation that it is off. Retain last reported state/freshness and the communication fault.

**Done when:** the dispatcher accepts mode-independent requests; fault/manual/automatic cases have explicit outcomes; only the authorised common path submits operational targets. Bench or simulated-transport evidence covers pending-command and reconnect cases.

### T07 — Isolate simulated inputs and development test controls

**Depends on:** T06 and T05R/T06R steps R0–R4; coordinate R5.
**Intent:** allow production builds to omit test functionality completely without duplicating the seasonal algorithm.

**Planning must settle:** how a profile selects exactly one evaluation-input provider, which current controls are operational versus test-only, and whether simulated evaluations can drive physical lamps.

**Work:**

- Make the seasonal calculation consume the T03 snapshot rather than directly reading a test-mode switch or test date/time entities.
- Supply real clock input in production. Supply live-or-simulated input through a development provider, selected without compiling test references into production.
- Move simulated date/time settings, test enable state and forced evaluation controls into development packages. Preserve useful test behaviour through the new boundary.
- Separate transport exercises from algorithm simulation. Keep normal manual lamp control distinct from fault injection or forced retries.
- Default development simulation to calculation-only or otherwise require explicit bench output enablement; document the chosen behaviour. Returning to real time must discard stale simulated targets and recalculate.
- Add checks for absent test IDs/entities/globals/generated references in production. Confirm development boot/reset cannot accidentally restore physical simulation output.

**Done when:** the production configuration and generated code have no dependency on test entities or simulated state; development simulation still exercises the same seasonal algorithm; transaction clocks remain real.

### T08 — Separate operational diagnostics from verbose development diagnostics

**Depends on:** T06–T07 and the T05R/T06R model; coordinate R5.
**Intent:** keep production understandable during faults without carrying all development reporting.

**Planning must settle:** a minimum health contract, reporting intervals, and which mode-specific calculated values are genuinely useful for normal operation.

**Work:**

- Retain connection state per lamp, clock validity, automatic/manual status, requested and reported levels, readback freshness/mismatch, pending work, failure counters and last successful transaction information where supportable.
- Keep mode-specific status with its owning mode; common diagnostics must not require seasonal IDs in schedule builds.
- Move verbose traces and detailed internal calculations to optional development packages. Choose production logging and entity intervals deliberately.
- Record expected Home Assistant entities for each profile, including intentional removals, and measure whether reporting materially changes load.

**Done when:** production faults can be diagnosed without installing test tools; common diagnostics compile independently of either engine's private state; profile entity inventories distinguish deliberate differences from accidental omissions.

**Implementation and evidence:** Operational health entities remain in production for both the legacy and generic topology profiles. Detailed seasonal calculations and per-fixture automatic previews are opt-in development packages; seasonal status entities are declared with the seasonal engine. Production logging is INFO and development logging is DEBUG. The [diagnostic profile inventories](docs/diagnostic-profiles.md) record intended entities and sampling cadence. PR #11 CI passed both workflow runs: production/development configurations validated and firmware compiled; generated-source checks confirmed representative operational entities are shared and verbose entities remain development-only. Physical controller and lamp load were not measured; the documented cadence is a configured sampling estimate, not a hardware/network measurement.

### T09 — Assemble and verify both seasonal profiles

**Depends on:** T07–T08.  
**Intent:** finish and prove the modular seasonal architecture before adding a new engine.

**Planning must settle:** the smallest explicit composition for production and development, numerical comparison tolerance, and the evidence needed to pass Gate A.

**Work:**

- Create `seasonal-production.yaml` and `seasonal-development.yaml` as supported entry points.
- Prefer a shared composition plus explicit input-provider/development additions. Do not layer development over production if doing so leaves both input providers or duplicate orchestrators active.
- Ensure each profile has one engine, one evaluation source and one output path.
- Validate/compile both in CI. Replay baseline fixtures and verify production/development parity when development uses live inputs.
- Verify expected Home Assistant entities, restored values and the absence of development functionality in production. Perform a focused seasonal bench smoke test.

**Done when:** Gate A has recorded evidence. Any intentional seasonal behaviour change is clearly distinguished from the modularisation; unresolved compatibility regressions are not carried into schedule development.

### T10 — Specify configurable schedule behaviour and edge cases

**Depends on:** T09.  
**Intent:** define what schedule mode means before implementing a second engine.

**Planning must settle:** the initial number of daily points/windows, whether each lamp has an independent schedule, step versus linear interpolation, ramp representation, and the intended configuration controls. A simple daily schedule is the initial scope; weekly calendars are deferred unless specifically selected here.

**Work:**

- Write `docs/schedule-behaviour.md` with concrete example schedules and expected outputs before/at/between/after points, separately for JungleDawn and ProT5.
- Define midnight wrapping, the interval before the first and after the last point, duplicate/out-of-order points, disabled windows and invalid levels.
- Choose local wall-clock versus fixed-time semantics. Define outcomes for daylight-saving skipped/repeated times, clock corrections and startup part-way through a schedule.
- Choose validated runtime settings, persistence and how an edit becomes active. Prefer a complete valid schedule snapshot over acting on half-edited settings.
- Specify how common maximums, manual overrides, automatic disable and invalid-clock policy apply without duplication or double scaling.

**Done when:** expected outputs can be determined from the specification without guessing. All boundary cases have an explicit policy and test examples; the scope fits the agreed configuration interface.

### T11 — Implement schedule mode behind the same control contract

**Depends on:** T10.  
**Intent:** add schedule capability without modifying the seasonal implementation or embedding schedule knowledge in BLE.

**Planning must settle:** entity layout, persistence format, evaluation cadence and a bounded implementation of the agreed interpolation/ramp behaviour.

**Work:**

- Implement the schedule engine, runtime settings and validation from T10. Produce both lamp targets through the T03 contract.
- Use the shared real/development evaluation-input boundary where practical. Add only schedule-specific development controls that cannot be expressed through it.
- Create schedule production/development profiles and standalone build fixtures.
- Recalculate from the current evaluation time so startup or a missed update does not depend on having observed every earlier time event.
- Add tests for specified boundaries, edits, invalid schedules and maximum-level handling. Rerun seasonal regression checks if shared code changes.

**Done when:** both schedule profiles validate/compile and meet T10's examples; production schedule builds have no seasonal calculation entities/state or development test controls; BLE code remains mode-independent.

### T12 — Enforce the four-profile build and regression matrix

**Depends on:** T11.  
**Intent:** prevent changes that work only in the developer's current profile.

**Planning must settle:** the required CI jobs, profile-content assertions and which behaviour can be checked off-device versus requiring a bench.

**Work:**

- Run configuration validation and full ESP32-C3 compilation for all four profiles on the pinned supported toolchain.
- Extend coverage using the T05R/T06R topology matrix: repeated products, swapped/sparse slots, shared/independent groups and expected-invalid configurations. Keep compiled versus physically verified topology support distinct.
- Use local includes from the checked-out commit. Keep separate, explicit checks for consumption through a remote Git reference.
- Check expected entity/component inventories and mutually exclusive providers/engines. Detect production references to test-only state and unintended seasonal/schedule cross-dependencies.
- Run meaningful deterministic cases from the baseline and schedule specifications. Avoid tests that merely duplicate the implementation's arithmetic without an independent expected result.
- Record firmware size and relevant compiler warnings; fail on defined limits or unexplained regressions. Compile-time size does not establish runtime heap headroom.
- Use dummy credentials and sanitised output for CI. Ensure artifacts/logs cannot contain a live device's expanded secrets.

**Done when:** a broken supported profile blocks the change, and CI output identifies the affected profile and check. Hardware-only requirements remain visible instead of being represented as automated passes.

### T13 — Add project identity, compatibility policy and release metadata

**Depends on:** T12.  
**Intent:** make a running controller and its source/configuration compatibility identifiable.

**Planning must settle:** project namespace, first modular version, one source of version truth, minimum supported ESPHome version, and whether profile changes affect persisted configuration compatibility.

**Work:**

- Add stable project identity and release version metadata. Expose the built profile/mode as read-only information; do not imply runtime mode switching exists.
- Set `min_version` from actual requirements and supported-build evidence. Document the pinned development/CI version separately from the minimum.
- Make firmware/project version and ESPHome version discoverable through documented diagnostics/device information; verify how Home Assistant displays them.
- Define semantic-versioning expectations for substitutions, entities, persistence and behaviour. Add `CHANGELOG.md` and a release checklist.
- Keep project update hooks observational initially. Do not silently reset calibration, change schedules or enable automatic control after a version change.

**Done when:** firmware identity, selected profile, source release and supported toolchain can be correlated; metadata is consistent across profiles; update behaviour preserves settings unless an explicit migration says otherwise.

### T14 — Create minimal device examples and installation documentation

**Depends on:** T13.  
**Intent:** make the modular project usable without knowledge of its internal file split.

**Planning must settle:** the public substitution contract, recommended initial profile, local file names and the manual commissioning sequence.

**Work:**

- Provide a minimal example for each supported profile, or one fully documented template with unambiguous profile alternatives. Include identity, timezone, lamp MAC inputs and a pinned package reference.
- Add `secrets.example.yaml` with clearly non-live values. Explain generation of valid API credentials; distinguish explanatory placeholders from CI's valid dummy inputs.
- Document explicit fixture/group/context mapping and the legacy pair adapter, validation/compile/install steps, Home Assistant setup, per-fixture calibration, readback verification and enabling automatic control.
- Explain production versus development, ordinary manual override, mode changes by rebuild, settings migration and return to a previous release.
- Build from a clean consumer directory using a reachable candidate commit/ref. Confirm nested includes and any helper/header assets work without a local repository beside the device YAML.
- Keep internal package references on the same checkout/revision; avoid a candidate profile pulling dependencies from an older tag or moving branch.

**Done when:** a controller needs only installation data and one profile selection; the remote consumer build succeeds; the instructions contain no requirement to copy algorithm/dispatcher sections.

### T15 — Validate hardware behaviour, resource headroom and upgrade compatibility

**Depends on:** T12–T14.  
**Intent:** establish operational evidence before declaring a modular release stable.

**Planning must settle:** bench hardware, representative runtime settings, observation duration, acceptable resource margins and stopping/rollback criteria. Choose these before seeing results.

**Work:**

- Exercise both lamps through low/medium/high/off levels, automatic/manual transitions, pending-command changes, readback, power cycling, disconnect/reconnect, time loss/recovery and Wi-Fi/API loss.
- Check expected output after reboot, after interrupted communication and when one lamp remains unavailable. Confirm reported state reflects evidence rather than the most recent request.
- Check seasonal golden cases and schedule boundaries on-device. Verify development simulation/transport tools do not bypass common operating limits unintentionally.
- Measure flash/OTA partition margin and runtime memory under connection, reconnect, reporting and OTA workloads. Record minimum free heap and fragmentation indicators where available, plus resets/watchdog events and responsiveness.
- Exercise all four profiles with comparable instrumentation/settings. Attribute differences cautiously; extra diagnostics themselves consume resources. Do not claim a dual-engine runtime build would or would not fit without measuring one.
- Test baseline-to-modular upgrade, development-to-production transition and documented profile changes. Verify calibration, settings, Home Assistant identity/automations and stale test state; preserving an ESPHome ID alone is not proof of persistence compatibility.
- Rehearse recovery/rollback, including any limits caused by changed stored settings. Check autonomous behaviour when Home Assistant is unavailable.

**Done when:** a hardware report gives actual results and resource margins for each advertised profile, with no unexplained regression. Recovery is demonstrated, and any unsupported migration or physical fault limitation is documented.

### T16 — Publish the first verified modular release

**Depends on:** T15.  
**Intent:** provide an immutable, reproducible source version for real deployments.

**Planning must settle:** version number, release contents, exact candidate commit and how final remote-reference validation happens before stable promotion.

**Work:**

- Assemble release notes covering profile support, tested hardware/toolchain, intentional entity or behaviour changes, migration steps and known limitations.
- Run the required matrix on the final candidate; ensure metadata and documentation describe that candidate.
- Use a candidate ref to rehearse remote consumption, then create the stable tag on the verified source and verify resolution/build through that tag before recommending it.
- Treat published stable tags as immutable. Changes after tagging require a new version; do not rewrite a tag to make a failed release look successful.
- Publish source/configuration artifacts as appropriate. Keep device-specific credential-bearing binaries private; generic bootstrap binaries are a later deliverable.

**Done when:** the stable release has traceable checks and a working pinned consumer example. A GitHub source update alone does not change any running controller; upgrades remain deliberate build/install operations.

### T17 — Migrate the existing controller and provision a second controller

**Depends on:** T16.  
**Intent:** prove the project works both as an upgrade and as a reusable installation.

**Planning must settle:** deployment window, observation period, enclosure-specific settings and rollback triggers. Use the verified recovery procedure from T15.

**Work:**

- Convert the existing Skink device configuration to a small wrapper using the stable seasonal profile and its existing identity/private values.
- Validate, compile, install and verify settings, entities, both lamp readbacks and an agreed operating cycle. Keep development features off for the production installation.
- Configure a fresh ESP32-C3 from the example using only a new device YAML and local credentials/MAC values. Do not copy implementation sections.
- Verify the controllers target their intended lamps and remain independently configurable. Use an appropriate bench setup if a second live enclosure is not available.
- Record each installed device's profile, release, relevant settings and outcome. Feed any installation friction back into the examples and documentation.

**Done when:** Gate B is met by actual upgrade and fresh-install evidence. A second-device failure is resolved in the shared project or documentation rather than by an undocumented per-device fork.

### T18 — Design bootstrap, adoption and commissioning as distinct states

**Depends on:** T17.  
**Intent:** add convenient first-time setup without treating an unconfigured controller as ready to operate lamps.

**Planning must settle:** bootstrap composition, how the user chooses a final profile, how lamp addresses are supplied, and how the uncommissioned state is represented and enforced.

**Work:**

- Define the state sequence: generic firmware → Wi-Fi configured → discovered/adopted → local configuration completed → production firmware installed → settings/readback checked → automatic control enabled.
- Choose either a minimal bootstrap that contains no lamp transport, or a full controller whose uncommissioned state blocks all operational commands. Prefer the smaller option unless retaining the full controller materially simplifies adoption.
- Define a compileable adoption entry point without installation-specific secrets. If placeholder MACs are used, establish a separate commissioning interlock; placeholders alone are not a safety mechanism.
- Decide how the generated local configuration selects seasonal versus schedule production and supplies both real MAC addresses. Build-time mode selection remains the contract.
- Choose supported provisioning methods based on the actual board: captive portal and/or Improv Serial initially; BLE Improv only after confirming coexistence/resource behaviour with the lamp clients.
- Define network credentials, API/OTA access and setup access-point handling through adoption, reboot and recovery. Avoid distributing shared production credentials.

**Done when:** a short design specifies every transition, the required local edits and the exact point at which lamp operation becomes possible. Dynamic BLE discovery/pairing is explicitly outside this phase.

### T19 — Implement and test generic provisioning firmware

**Depends on:** T18.  
**Intent:** allow the same credential-free initial firmware to be installed on multiple compatible controllers.

**Planning must settle:** supported USB/serial path, unique device naming, provisioning methods actually selected, and setup timeout/recovery behaviour.

**Work:**

- Add a bootstrap entry point with the project identity and unique device naming. Do not apply automatic naming changes to the existing production device as a side effect.
- Implement the chosen captive portal/Improv mechanisms and required API/OTA support. Include only the provisioning paths that are tested and documented.
- Test two fresh or reset boards for unique discovery and correct credential retention after reboot, including mistyped Wi-Fi details and a changed network.
- Prove the uncommissioned state cannot transmit operational lamp requests, including through manual controls or restored state if the bootstrap includes them.
- Measure bootstrap memory and OTA behaviour separately. If BLE provisioning is included, test its coexistence with the full controller wherever it remains installed.

**Done when:** one generic firmware provisions two boards independently, contains no installation credentials and has a demonstrated recovery path. The uncommissioned output restriction is verified rather than inferred.

### T20 — Implement dashboard adoption and explicit lamp commissioning

**Depends on:** T19.  
**Intent:** have Device Builder create a small maintainable local configuration that remains tied to the shared project.

**Planning must settle:** exact public adoption URL/ref, required/default substitutions, generated local naming, and whether separate mode-specific adoption entry points are necessary.

**Work:**

- Add `dashboard_import` with a public, versioned import location and `import_full_config: false`. Ensure the advertised project identity, import configuration and bootstrap version agree.
- Test actual discovery and adoption in Device Builder; inspect the YAML it generates. Do not assume all desired substitutions or secrets are automatically written into it.
- Prove the immediately adopted configuration validates and compiles in its defined uncommissioned state without missing private lookups.
- Document and test supplying the supported fixture topology and each enabled fixture's real MAC address, selecting the final production profile and installing the commissioned build.
- Verify device identity, credentials and OTA access across bootstrap-to-production transition. Confirm the chosen release stays pinned and every enabled fixture is explicitly checked before automatic control is enabled.
- Test incomplete/invalid commissioning values and recovery from an interrupted install. No hidden edits to upstream packages should be necessary.

**Done when:** actual generated YAML plus the documented local edits completes adoption for each supported production mode. An adopted-but-uncommissioned controller remains non-operational, and production excludes development test features.

### T21 — Extend CI and release checks to bootstrap and adoption artifacts

**Depends on:** T20.  
**Intent:** make provisioning repeatable across releases without weakening the existing profile checks.

**Planning must settle:** public artifact types, artifact naming, firmware/release metadata sources and which end-to-end checks require a hardware release checklist.

**Work:**

- Add standalone validation/compile fixtures for bootstrap and every advertised adoption entry point, including the default uncommissioned configuration.
- Keep the four runtime profile jobs and behaviour checks. Add assertions for commissioning interlocks and the absence of private credentials in distributable source/artifacts.
- Check import URLs and candidate/stable refs resolve to the intended version; prevent mismatches between bootstrap metadata, adoption entry point and nested package sources.
- If distributing binaries, produce the correct artifacts for first serial installation and supported OTA paths, with checksums, supported board/flash information and traceable build versions.
- Do not assume a source change rebuilds or updates already installed devices. State the exact release and update process.

**Done when:** a release cannot be promoted with a broken public import or missing bootstrap build, and hardware adoption checks remain explicit release requirements. Public binaries are generic rather than exported from a configured live device.

### T22 — Rehearse a fresh installation and release the adoption workflow

**Depends on:** T21.  
**Intent:** confirm the documented experience works for someone who did not build the package internals.

**Planning must settle:** representative first-time installer, clean Device Builder environment, chosen pilot hardware and the final release checklist.

**Work:**

- Start with a blank/reset compatible board and follow only the instructions: flash, provision Wi-Fi, discover, adopt, supply MACs/select profile, compile/install, check limits/readback and enable automatic control.
- Repeat the profile-specific parts for both seasonal and schedule production. Confirm no test entities appear and only the selected engine's settings are offered.
- Rehearse a normal update to a newer pinned release and return to the documented recovery path. Check identity and settings retention.
- Finish README/onboarding documentation, troubleshooting for discovery/Wi-Fi/MAC/time/readback issues, profile-change guidance and release notes.
- Promote the tested adoption release using the same immutable-version discipline as T16. Record pilot outcomes and remaining limitations.

**Done when:** Gate C is satisfied from a clean starting point, all required edits are documented, and the manual package installation route remains usable alongside adoption.

### T23 — Add temporary daily maximum and timed fixed level

**Depends on:** T09 and Gate A only. This task can proceed independently of T10–T22.

**Intent:** allow a Home Assistant user to hold one fixture below today's automatic curve or at a chosen fixed level for a bounded time, then return it to current automatic output.

**Requirements:** [temporary lighting feature request](docs/temporary-lighting-requirements.md).

**Implementation:** [post-T09 implementation plan](docs/plans/temporary-lighting-implementation.md).

**Software implementation:** added on branch `t23-codex`; deterministic policy tests, seasonal production/development profile builds, input-isolation checks, diagnostic inventory, and no-override seasonal parity pass. User workflow is documented in the README. Review hardening covers quarter-hour validation, history-based cap release, transition-wide authorization revocation, stale readback and bounded correction retries. The production policy lambda has a deterministic regression harness. See the [planned ESP32-C3 bench session](docs/plans/t23-bench-validation.md) for the remaining evidence.

**Done when:** the requirements' acceptance cases and physical BLE/readback behavior are recorded on the ESP32-C3 bench. That hardware evidence remains outstanding; the checkbox stays open until then. The normal seasonal calculator and permanent calibration remain unchanged.

## Decisions to carry into planning

These are unresolved inputs, not reasons to delay creating the repository or capturing the baseline.

| Decision | Resolve in | Default direction |
| --- | --- | --- |
| Exact deployed source, board and toolchain | T01–T02 | Preserve the current working baseline first |
| Repository identity, visibility and licence | T02 | Choose deliberately before publishing |
| Interface implementation and ownership | T03 | Small explicit contract; one shared output path |
| Invalid clock, manual override and restore policy | T06 | Preserve verified behaviour; isolate any policy changes |
| Whether simulation may drive real lamps | T07 | Calculation-only by default; explicit bench enablement |
| Schedule point model and interpolation | T10 | Bounded configurable daily schedule |
| DST, midnight wrapping and edit activation | T10 | Explicit examples before implementation |
| Minimum ESPHome version and supported pin | T02, confirmed T13 | Evidence-based minimum and reproducible build version |
| Runtime memory/flash acceptance margins | T15 | Measure the actual hardware/workloads |
| Minimal bootstrap versus gated full controller | T18 | Prefer minimal bootstrap unless proven inconvenient |
| Provisioning methods and mode selection after adoption | T18–T20 | Test a small supported set; explicit local commissioning |

## Deferred work

Do not allow these to expand the initial implementation accidentally. Revisit after the relevant release has operational evidence.

- Runtime switching between seasonal and schedule engines. If wanted later, prototype both engines together and measure flash, minimum heap, responsiveness and transition correctness; the present recommendation is not proof that the ESP32-C3 cannot support it.
- Dynamic BLE scanning, lamp selection and persistent runtime pairing.
- More than four fixtures, runtime topology discovery and broad board/framework support. Up to four static fixtures and repeated products are now in the T05R/T06R plan; more-than-two production support still requires hardware evidence.
- Additional engines such as Home Assistant-driven or manual-only profiles.
- Weekly/holiday calendars or substantially more elaborate scheduling than T10 defines.
- A web installer, automatic fleet updates or a separate runtime settings UI.
- Automatic migrations of calibration or animal-environment settings on project update.
- Rewriting the whole controller as an external ESPHome component merely to obtain modular files. Consider small helpers only where they clarify ownership or enable meaningful tests.

## Technical reference notes

Official documentation checked on 29 September 2026. Recheck relevant behaviour against the pinned ESPHome version when implementing; these references are not a substitute for compiling the actual profiles.

- [ESPHome packages](https://esphome.io/components/packages/): package configuration is merged; component IDs and list composition matter. The documentation covers conditional inclusion, dynamic include filenames and Git refs. Remote packages must use substitutions instead of secret lookups. This plan favours explicit profiles and checks the resolved configuration.
- [Sharing ESPHome devices](https://esphome.io/guides/creators/): documents creator metadata, provisioning and dashboard import. `import_full_config: false` references an upstream package rather than importing the entire implementation. The exact local YAML and commissioning flow must still be exercised in Device Builder.
- [ESPHome core configuration](https://esphome.io/components/esphome/): documents project identity/version, update hooks, `name_add_mac_suffix` and `min_version`. A minimum version is a compatibility floor, not a build-environment lock.

Earlier conversation snippets were conceptual examples. Do not copy their placeholder repository URLs, version numbers, MAC addresses or provisioning settings into a production release without resolving the corresponding task.
