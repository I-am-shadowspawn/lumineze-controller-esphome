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

- [ ] **T13.1 — Identity and compatibility decision record.** Inventory existing
  substitutions, entities, preference fingerprints, tags and minimum platform
  APIs. Choose project namespace, version truth and profile identifiers. Define
  compatible versus breaking changes to topology, HA entities, storage, output
  behavior and public package paths. Acceptance: explicit legacy-to-generic and
  seasonal-to-schedule rules; a stable YAML ID alone is not treated as restored
  identity proof.
- [ ] **T13.2 — Metadata composition.** Add shared project name/version and
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
