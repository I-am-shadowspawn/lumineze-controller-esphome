# T05 — Mechanical module extraction

Historical completion evidence. The subsequent, unimplemented T05R topology
refactor is specified in the [architecture](plans/fixture-topology-architecture.md)
and [runbook](plans/fixture-topology-implementation.md); do not treat the two-client
inventory below as a constraint on the new design.

Source: `master` at `b92812f`, ESPHome 2026.9.0 / ESP-IDF 5.5.5. T01–T04 and the ownership contract in `docs/architecture.md` are prerequisites. This task moves the existing YAML without changing identifiers, values, expressions or automations. Policy and production/development separation remain T06–T09 work.

## Extraction order and temporary grouping

Keep `packages/lumineze-controller.yaml` as the public entry point. It composes local fragments in the order below. Each original top-level component list stays in one fragment, except `script`, whose three contiguous ranges remain in original order. This avoids changing entity order or merging entries with duplicate IDs during a mechanical move.

| Package | Original content | Temporary cross-references |
| --- | --- | --- |
| `core/base.yaml` | substitutions, `esphome`, `esp32`, `logger`, `api`, `ota`, `wifi` | Device identity and platform defaults; local YAML still owns secrets |
| `core/time.yaml` | both `time` entries | Publishes `controller_last_time_source` from diagnostics |
| `core/ble.yaml` | `esp32_ble`, `esp32_ble_tracker`, both `ble_client` entries | Callbacks update dispatcher state and diagnostics |
| `core/state.yaml` | full `globals` list | Dispatcher, seasonal and safety globals remain together to preserve list order; T06 can separate owners |
| `features/diagnostics.yaml` | complete `binary_sensor`, `sensor`, `text_sensor` lists | BLE notifications and seasonal status remain here temporarily to preserve entity order; T08 separates production/verbose diagnostics |
| `core/controls.yaml` | complete `switch`, `number`, `button` lists | Test and seasonal settings remain here temporarily; T06/T07 separate policy and development controls |
| `modes/seasonal.yaml` | `calculate_solar` script, unchanged | Still calls the shared queue and reads test/control IDs; T06/T07 address this |
| `core/dispatcher.yaml` | `queue_lumenize_command`, `record_ble_failure`, `dispatcher_tick`, full `interval` list | Owns command state and the single 1-second timeout/dispatch tick; 10-second evaluation hook remains in this list until T06 |
| `lamps/protocol.yaml` | both lamp transaction scripts | Encodes existing BLE writes/readback and refers to fixed client IDs |

`script` order is seasonal → dispatcher → lamp transactions, exactly as in the monolith. The package includes are local to the checked-out repository. The existing remote-Git entry point must also resolve those relative includes; test it from a pushed branch before completion.

### Module interfaces at this checkpoint

- `core/base.yaml` owns no explicit IDs. It takes local substitutions for identity, timezone, MACs and enable flags, and provides platform, API/OTA and Wi-Fi defaults. Local device YAML supplies credentials.
- `core/time.yaml` owns `controller_time` and `homeassistant_time`. It takes the timezone substitution and external clock updates, then publishes the last-sync-source diagnostic through `controller_last_time_source`.
- `core/ble.yaml` owns `jungle_dawn_client` and `prot5_client`. It takes the MAC substitutions and dispatcher state, then publishes connection callbacks and failure requests. `esp32_ble_tracker` is declared only here.
- `core/state.yaml` owns the 53 existing global IDs, listed by intended owner in `docs/architecture.md`. It takes no external configuration; other modules read/write this shared state until T06 narrows their interfaces.
- `features/diagnostics.yaml` owns all 16 binary sensors, 29 sensors and 19 text sensors, including 23 explicit IDs. It reads shared state/time and publishes user-facing and internal diagnostics; the two notification sensors also write readback state as in the baseline.
- `core/controls.yaml` owns all six switches, 26 numbers and four buttons, including 32 explicit IDs. It receives Home Assistant control changes and invokes `calculate_solar` or `queue_lumenize_command`. Test controls remain present until T07.
- `modes/seasonal.yaml` owns `calculate_solar`. It reads time, seasonal settings, switches and state; it updates solar/curve globals, status text and queue decisions. Direct queue references remain until T06.
- `core/dispatcher.yaml` owns `queue_lumenize_command`, `record_ble_failure`, `dispatcher_tick` and both interval entries. It takes authorised target requests and transport feedback, updates transaction/retry state and selects a lamp transaction. It still calls the seasonal evaluation every 10 seconds.
- `lamps/protocol.yaml` owns `jungle_dawn_transaction` and `prot5_transaction`. It takes the selected target and fixed BLE client IDs, sends existing wire commands, requests readback and records completion or failure.

## Validation plan

1. Capture the resolved one-light and two-light CI configurations before moving anything. Compare parsed mappings/lists after each extraction; ignore only source-location metadata and mapping-key order, not list order or scalar values.
2. Check for exactly two BLE clients, one 10-second evaluation interval, one 1-second dispatcher interval, and no duplicate `on_time_sync`/BLE callbacks or `on_boot` hook.
3. Validate and fully compile the two-light fixture locally on the pinned toolchain. Confirm the one-light fixture still validates and compare generated entity/restore inventories to the baseline.
4. Push the branch and validate a temporary local device YAML that imports the public entry point as a remote Git package from that branch. Wait for the PR's full-build CI.

No deployed controller is flashed in this task. T01's live output/heap/recovery observations remain a separate Gate A requirement.

## Local extraction evidence

Both one-light and two-light CI fixtures validated with ESPHome 2026.9.0. After the move, each resolved configuration parsed identically to its pre-move snapshot: same list order, scalars, entity names, IDs, restore settings, limits, scripts and callbacks. The two-light result contains exactly two BLE clients, the original 10-second and 1-second intervals, one sync callback per clock, one connect/disconnect callback per BLE client, and no boot hook. A full local two-light ESP32-C3 compile passed with ESP-IDF 5.5.5: image 1,438,982 bytes, static RAM estimate 148,380 bytes. The earlier T04 fixture image was 1,438,754 bytes; resolved YAML is identical, so this small binary-size difference is not evidence of a YAML behaviour change.

A temporary device YAML importing the pushed branch through the remote Git package URL validated, including all nested relative includes. Its parsed resolved configuration matched the pre-extraction two-light snapshot exactly. GitHub's full-build checks passed on both the [branch push](https://github.com/I-am-shadowspawn/lumineze-controller-esphome/actions/runs/36604028492) and [pull request](https://github.com/I-am-shadowspawn/lumineze-controller-esphome/actions/runs/36604101735). This completes the T05 source/compile comparison; it does not replace Gate A hardware observations.
