# Remote installation contract (candidate 2.0)

This is the public YAML boundary for the generic controller. It targets an
ESP32-C3 running ESP-IDF with ESPHome 2026.9.0. Software validation is recorded
in `docs/evidence/`; physical release remains subject to Gate A and T15.
Choose exactly one profile at build time:

| Profile package | Engine | Input | Extra fixture fragment |
| --- | --- | --- | --- |
| `packages/seasonal-production.yaml` | Seasonal solar curve | Real clock | Seasonal temporary controls are in `fixture-luminize.yaml` |
| `packages/seasonal-development.yaml` | Seasonal solar curve | Simulated clock | `fixture-luminize-development.yaml` per enabled fixture |
| `packages/schedule-production.yaml` | User schedule | Real clock | Use `fixture-luminize-schedule.yaml` |
| `packages/schedule-development.yaml` | User schedule | Simulated clock | `fixture-luminize-schedule.yaml` plus `fixture-luminize-development.yaml` per enabled fixture |

The local wrapper supplies `device_name`, `friendly_name`, `area_name`, and
`timezone` substitutions. The name must meet ESPHome's device-name rules; use
unique names for multiple controllers. `timezone` is the local IANA timezone
used by the real clock, for example `Europe/London`. The wrapper supplies Wi-Fi
SSID/password, a unique Home Assistant API encryption key, and the actual MAC
address of every enabled lamp from a private `secrets.yaml`. OTA can use a
private password if configured. Keep real secrets out of Git.

## Composition

The `packages` Git entry and the `lumineze_topology` external component Git
entry must use the **same immutable full commit SHA or verified release tag**.
Use the profile package once, followed by one context fragment per context,
one group fragment per group, and one fixture fragment per enabled fixture.
ESPHome Git package `files` entries with `path` and `vars` permit repeated
fragments. `context_id` and `context_name` feed context fragments;
`group_id` and `group_name` feed group fragments; `fixture_id`,
`fixture_name`, `fixture_mac`, and `fixture_default_maximum` feed fixture
fragments. Set the default maximum to **0 for ProT5** until calibrated, and
typically 100 for JungleDawn. The optional development fixture fragment
uses `fixture_id` and `fixture_name`.

Use `context-seasonal.yaml` with seasonal profiles. Use
`context-schedule.yaml` with schedule profiles, plus exactly one
`context-schedule-role.yaml` for each `visible` or `uv` role used by that
context. Schedule editors start unconfigured; configure and Apply in Home
Assistant before enabling automatic output. Do not include unused role editors.

`lumineze_topology` repeats the static topology as descriptors:

| Field | Meaning |
| --- | --- |
| `topology_version: 1` | Current descriptor format. |
| `engine_family` | `seasonal` or `schedule`; match the selected profile. |
| `input_provider` | `real` or `development`; match the selected profile. |
| `contexts` | One or two distinct `{id}` entries. |
| `groups` | One to four distinct `{id, context, output}` entries; `output` is `visible` or `uv`. Every context must have a group. |
| `fixtures` | One to four distinct `{id, slot, type, group, mac}` entries. Slots are integers 0–3 and must be unique. Every group must have an enabled fixture. |
| `allow_experimental_topology` | Set `true` only for three or four enabled fixtures; these layouts are experimental. |

All IDs across contexts, groups and fixtures must be distinct lowercase
letters, digits or underscores, beginning with a letter. Fixture `type` is
`jungle_dawn` (visible) or `prot5` (UV), and its group's `output` must match.
The MAC must be a unique, real six-byte address. The physical slot is an
installation choice; slot 0 is not reserved for a product. One or two enabled
fixtures are the ordinary software-validated range. Three or four require
the experimental flag and are not a supported physical installation.

To reserve a slot, declare only `{id, slot, enabled: false}` (optional
`location` is allowed). A disabled descriptor has **no** `mac`, `group`, or
`type`, and has no fixture package/BLE client. Do not use a missing MAC as an
enable switch. Each enabled descriptor requires one matching fixture package;
the build rejects mismatched BLE clients, transaction scripts, groups, roles,
and duplicated addresses. Changing any identity, slot, product, MAC, group,
role, or engine requires a rebuild. Home Assistant controls cannot change
topology at runtime. Calibration storage is tied to assignment identity, so
record settings before changing an assignment.

The legacy `packages/lumineze-controller.yaml` adapter with
`enable_jungle_dawn`/`enable_prot5` remains for v1-style installations. It is
not a generic topology wrapper; use `example/vivarium-example.yaml` for the
v1.0.0 recovery reference and `docs/compatibility.md` for migration limits.
