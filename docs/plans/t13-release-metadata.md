# T13 — Identity, compatibility and version metadata

**Entry/dependencies:** T12 matrix working. Policy and inventory planning can
proceed now. **Delivery:** consistent build identity plus documented compatibility
and release rules; no release promotion or device installation.

## Implementation direction

Use one checked-in shared project metadata fragment as version truth, with a
stable project namespace and per-profile read-only identity. Choose its namespace
and actual version after inspecting current tags and installed devices. Existing
`v1.0.0` and `v1.9.0-rc` tags are recovery/candidate history, not evidence that a
new modular release passed Gate B. Never rewrite those tags. Build identity must
correlate profile + project version + ESPHome version with a manifest/source SHA;
consumers must not invent or automatically inherit a moving-branch version.

## Incremental deliveries

- [x] **T13.1 — Identity and compatibility decision record.** Inventory existing
  substitutions, entities, preference fingerprints, tags and minimum platform
  APIs. Choose project namespace, version truth and profile identifiers. Define
  compatible versus breaking changes to topology, HA entities, storage, output
  behavior and public package paths. Acceptance: explicit legacy-to-generic and
  seasonal-to-schedule rules; a stable YAML ID alone is not treated as restored
  identity proof.
- [x] **T13.2 — Metadata composition.** Add shared project name/version and
  read-only built profile information to all four profiles without activating
  controls. Ensure a legacy compatibility build is labelled accurately, not
  presented as a generic profile. Acceptance: resolved configs and builds agree
  on version and namespace; runtime profile cannot be edited into another engine;
  existing preference/entity names remain intact unless migration is documented.
- [ ] **T13.3 — Supported-toolchain policy.** Determine `min_version` from the
  actual required features and builds; retain a separate recommended CI pin.
  Test the chosen minimum and current supported pin across advertised profiles
  or state that only the pin is initially supported. Acceptance: no guessed
  minimum or unsupported ESP-IDF/board claim; record matrix results and dependency
  update procedure. Keep dependency upgrades separate from metadata changes.
- [ ] **T13.4 — Diagnostics and update behavior.** Verify firmware/profile and
  ESPHome identities in HA/device information on bench. Add observational update
  hooks only if needed; never reset maxima/schedules or enable automatic output
  on an update. Acceptance: metadata survives profile rebuilds with documented
  identity, and boot/update controls remain off as required. Software inventory
  can pass earlier; record HA display observations as pending until captured.
- [ ] **T13.5 — Release documentation and consistency checks.** Add changelog,
  compatibility table and release checklist. CI rejects mismatched version/profile
  metadata; release manifests tie versions to SHAs and hardware evidence. Define
  major/minor/patch expectations, storage rollback limits and immutable-tag
  policy. Acceptance: a deliberate version mismatch fails its check; readers
  can identify support status, source and migration from a running device.

## Completion and rollback

Complete only after metadata checks and runtime identity evidence are recorded.
No automatic settings migration is introduced here. Roll back a metadata change
without overwriting lamp calibration or silently changing the active engine.

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


### T13.1 — complete

Source `fd8d778`. Repository tags are `v1.0.0` and `v1.9.0-rc`; neither base declares
project identity. Supplied deployed wrapper/Builder version are source context,
not a live inventory. Chose `shadowspawn.lumineze` / `2.0.0-dev` unreleased identity,
shared version truth, four generic profile IDs and explicit legacy labels.
`docs/compatibility.md` records topology, entity-name/preference, calibration and
schema-1 schedule boundaries; legacy/profile migration and rollback are explicit,
not automatic. Only ESPHome 2026.9.0 / observed IDF 5.5.5 is initially qualified.
No tags or installed devices changed. Next: metadata composition and checks.


### T13.2 — in progress

- [x] **T13.2a — Shared metadata and read-only diagnostics.**
  `core/project.yaml` holds the namespace/version/minimum and four read-only
  diagnostics. Generic profiles identify their engine/provider flavour; legacy
  wrappers are explicitly labelled legacy. The component recovers its actual Git
  SHA and marks changed firmware assets dirty, or reports unknown without its
  own Git root. Package/component pin equality remains the consumer contract.
  Six resolved configurations pass identity checks. Existing seasonal inventory
  entries remain exact; only four explicitly checked diagnostics are added.
  Schedule production compiles and its generated project/profile/source identity
  passes (`/tmp/t13-schedule-build.log`, RAM 148,064 / flash 1,256,208 bytes).
- [x] **T13.2b — All-profile compiled identity proof.** Build all four from the
  clean committed source and compare namespace/version/profile/SHA; integrate
  metadata checks in CI. No live HA display proof is claimed.


T13.2b complete: all four generic and both legacy compatibility builds compile
with the shared namespace/version. The six generated builds were checked against
resolved profile IDs and, for generic profiles, the exact clean source SHA
`a14c958c63891fd8e06b75a9b1d287b7bc165fcf`; legacy reference text is
explicitly unverified. Local build logs are `/tmp/t13-{seasonal,schedule}-*
build.log` and `/tmp/t13-legacy-{production,development}-build.log`.
`check_project_metadata.py` now runs in CI against all six configurations and
against each compiled job. Seasonal pre-T11 inventory is unchanged apart from
four documented read-only metadata entities. Actual HA/device display and update
retention remain T13.4/T15 physical evidence.
