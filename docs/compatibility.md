# Build identity and compatibility policy

## Candidate identity

The modular candidate uses project namespace **`shadowspawn.lumineze`** and
version **`2.0.0-dev`**. Version truth is the shared project fragment; profile
identity distinguishes seasonal/schedule and production/development. This is an
unreleased software candidate. `v1.0.0` remains the recovery tag and `v1.9.0-rc`
remains candidate history. Those immutable tags are never rewritten.

No existing project namespace is declared in the repository's legacy or generic
base configuration. The supplied deployed wrapper also declares none. That is a
source inventory, not proof of the current device's HA information or settings.
T13.4/T15 must record actual device information before compatibility is accepted.

Generic firmware should report the external component's resolved Git SHA and
whether its checkout was modified. Pin package and component to the same full
SHA so this identifies the whole build. A local directory without Git metadata
reports unknown and cannot serve as release evidence. Legacy compatibility builds
must identify themselves as legacy, with an explicitly unverified source
reference where no component can recover the resolved SHA. The CI/release build
manifest records actual source SHA and toolchain for every build.

## Compatibility boundaries

| Change | Rule | Required action/evidence |
| --- | --- | --- |
| Patch to diagnostics/docs without changed IDs or output/storage behavior | Patch candidate | Full affected software gates; retain physical support limits |
| New optional capability with existing behavior unchanged | Minor candidate | Capability matrix, complete advertised builds and bench cases |
| Changed output policy, public paths/IDs, role semantics or incompatible storage | Major candidate | Migration and rollback instructions; explicit commissioning |
| Legacy fixed slots to generic topology | Explicit migration | Map both MACs, IDs, roles/groups/slots; re-enter and verify calibration; review HA automations |
| Seasonal to schedule or back | Rebuild/profile switch | Export settings, keep automatic/manual off, commission selected engine; no automatic conversion |
| Production to development or back | Rebuild/profile switch | Simulation gates start off; production omits test state; verify actual HA removals |
| Fixture label/group-only edit with unchanged fixture ID/slot/product/MAC | Calibration key unchanged | Runtime retention still needs upgrade evidence |
| Fixture ID/slot/product/MAC changes | Calibration assignment changes | Recommission maximum; ProT5 starts at zero |
| Schedule context ID or used-role mask changes | New preference namespace/fingerprint | Re-enter/apply complete schedules; do not reuse old data implicitly |
| Schedule schema 1 rebuild, same context ID/used-role mask | Defined compatible record | CRC/two-bank host proof plus actual persistence/upgrade bench proof |
| Unknown/corrupt schedule schema | No activation | Valid older bank may restore; otherwise unconfigured, controls off |

Generic calibration keys bind fixture ID, slot, product and normalized MAC.
Schedule fingerprints/bank keys bind schema namespace, context ID and used-role
mask. Entity number/switch preferences depend on ESPHome's sanitized entity names;
a YAML ID alone does not prove HA or persisted identity. Renaming labels can
change those independent preferences and HA entities. Keep an export before edits.

## Supported toolchain policy

Initially the only verified toolchain is **ESPHome 2026.9.0**, ESP-IDF **5.5.5** as
resolved by that pin, on **ESP32-C3**. The supported minimum is the tested pin;
older versions have not been qualified. Newer Device Builder versions require
all four profiles, compatibility gates and affected bench checks before being
advertised. `min_version` rejects older builders; it does not prove future versions.
Framework/ESPHome upgrades are separate changes from identity metadata.

## Rollback

Capture device YAML, immutable package/component refs, HA entity/automation
mapping, calibration and active schedule before updating. Never copy private
secrets into this repository. Preserve the working binary and recovery route.
Older seasonal firmware cannot interpret schedule records. Reverting code does
not automatically restore edited calibration, schedules or HA automations.
An incompatible storage change must explicitly document which data is retained,
ignored or reset. No metadata/update hook should enable lamps or reset settings.

Stable support and live migrations remain gated by T15–T17 evidence.
