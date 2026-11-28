# T21 — Extend CI and release checks to bootstrap and adoption artifacts

**Depends on:** T18 design, T19 bootstrap implementation and T20 adoption entry point.  
**Intent:** make provisioning and adoption repeatable across releases without weakening
existing profile checks.

**Status (in repo):** complete. T21.1/T21.2/T21.3 and the input-boundary part of
T21.4 are implemented and passing in-repo (see the CI section of
`docs/evidence/t19-t22-software.md`); binary artifact distribution (T21.4) and
the release checklist promotion step (T21.5) finalize at release time in T22,
when a T18-containing SHA exists to pin.

## Decisions already settled by T18–T20

- `firmware/bootstrap.yaml` is the minimal, lamp-transport-free image.
- `adopt/lumineze.yaml` is the `dashboard_import` entry point.
- `ci/bootstrap.yaml` and `ci/adopted-seasonal.yaml` are local CI fixtures.
- Placeholder MACs are coupled with the commissioning interlock.

## Remaining work

### T21.1 — Add bootstrap and adopted fixtures to CI validation

- Validate `ci/bootstrap.yaml`, `ci/adopted-seasonal.yaml` and a schedule-adopted fixture
  in the `validate` job.
- Compile `ci/bootstrap.yaml` and the adopted fixtures in the build job.
- Record sizes and confirm bootstrap is smaller than the full profiles.

### T21.2 — Add bootstrap/adoption-specific checks

- `scripts/check_bootstrap_isolation.py`: confirm the bootstrap resolved config has no
  `ble_client`, no `lumineze_topology.operational`, no fixtures, and bootstrap identity.
- `scripts/check_adopted_examples.py`: confirm the public adopted examples use one
  immutable SHA, include `adopt/lumineze.yaml`, include a profile package, and validate.
- `scripts/check_public_examples.py` already covers the four non-adopted wrappers.

### T21.3 — Manifest and release metadata

- Add bootstrap and adopted artifacts to `ci/profile-matrix.json` outside the four
  advertised profiles (the manifest must still list exactly the four runtime profiles).
- Ensure `scripts/check_profile_manifest.py` and `scripts/check_release_metadata.py`
  allow the extra keys without treating them as supported runtime profiles.
- Update release checklist to require bootstrap and adopted artifact checks before
  promotion.

### T21.4 — Secret and artifact boundary checks

- Confirm no live credentials are committed in bootstrap or adoption fixtures.
- Confirm CI artifacts for bootstrap do not contain fixture MACs.

### T21.5 — Handoff to T22

- Document which checks are automated and which remain hardware-only.
- Update `docs/bootstrap-adoption.md` with the CI status.

## Acceptance criteria

- A broken bootstrap or adopted example blocks the change.
- The four advertised runtime profiles remain the only entries in `profiles`.
- Bootstrap cannot accidentally include BLE lamp transport.
- Public adopted examples use consistent immutable refs.

## Exit condition

T21 is complete when CI runs the new checks and the release metadata accounts for
bootstrap/adoption artifacts. Physical Device Builder adoption is still T22.
