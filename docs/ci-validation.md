# CI validation and required checks

`ci/profile-matrix.json` is the coverage manifest. ESPHome is pinned by
`requirements-ci.txt`; dependency upgrades get their own review and all gates.

## Checks

- **Change scope:** always runs. A documentation-only update skips heavy jobs;
  an unknown comparison conservatively requests full checks. Manual and merge
  queue runs always validate firmware.
- **validate:** checkout-local behavioral/schema/compatibility regressions,
  legacy build regressions and topology builds. The validate job also
  validates and compiles the bootstrap fixture and the adopted
  (`adopt/lumineze.yaml` + profile) fixtures, asserts bootstrap isolation and
  its dummy-credential boundary, runs the adopted example contract with
  offline end-to-end resolution, and re-checks the four advertised profiles
  remain the only `profiles` manifest entries.
- **Profile / seasonal-production**, **Profile / seasonal-development**,
  **Profile / schedule-production**, **Profile / schedule-development**:
  independent build jobs, selected-engine/provider/capability inventories,
  source fault detection, static budgets and retained attempt logs. Only the
  four advertised runtime profiles appear in the build matrix;
  bootstrap/adoption artifacts are tracked separately under
  `adoption_artifacts` in `ci/profile-matrix.json`.
- **Immutable remote consumer:** ordinary Git package and component references
  on exactly the same candidate SHA, from an empty directory. PR/push checks
  compile schedule production; workflow dispatch rehearses all four profiles.
  The four classic public examples are re-validated against their pinned SHA
  first. Adopted public examples are verified offline in `validate`; after a
  T18-containing SHA is pushed, their `--remote` mode re-verifies them against
  the pinned GitHub SHAs during release rehearsal.
- **Required validation:** always reports. It succeeds for a verified docs-only
  skip or when every required software job succeeds; a failure/cancellation or
  failed change-scope job cannot become success.

Recommend requiring **Required validation** in branch protection after observing
its check name on a PR. Repository protection settings have not been changed.
Hardware Gate A/T23/T15 and release/deployment evidence remain separate approvals.

## Evidence and resilience

Heavy jobs are allowed to finish even when newer commits arrive; canceling an
older run can otherwise make a documentation-only baseline fail. A
documentation-only update leaves preceding firmware jobs active and its required
gate waits for the preceding commit’s successful Required validation check. Failed,
missing or still-pending source checks cannot be hidden by a documentation edit.

Profile jobs retain every compile attempt and a JSON summary for 14 days.
Three attempts wait 20/40 seconds and final failure remains failure. Do not delete
all framework/build caches between attempts. Cache identities include platform,
pin, profile and source inputs. Compile size budgets are 180,000 bytes static RAM
and 1,600,000 bytes flash on the current ESP32-C3 partition. Runtime heap still
requires measurements. Never treat a successful compile or requested BLE target
as physical confirmation.

CI fixtures contain dummy Wi-Fi and `AA:BB:CC:DD:EE:*` addresses. Inputs are checked
before retained build logging; only attempt logs and summary files may upload,
and upload requires the artifact boundary check to succeed. No deployment YAML,
secrets file or compiled firmware is uploaded by this workflow.

Run locally with the pinned ESPHome environment:

```sh
python scripts/check_profile_manifest.py
python scripts/check_fast_gates.py
python scripts/check_gate_faults.py
python scripts/check_schedule_schema.py esphome
python scripts/build_profile.py schedule-production
python scripts/check_remote_consumer.py --ref FULL_IMMUTABLE_SHA --all --compile
```

`check_gate_faults.py`, `check_build_gate_faults.py`, `check_build_resilience.py`
and `check_ci_change_scope.py` prove that broken outputs/generations, missing
profiles/private state, terminal download failures/budget breaches and invalid
workflow success paths are rejected. Faults run only in disposable copies or
in-memory inputs.
