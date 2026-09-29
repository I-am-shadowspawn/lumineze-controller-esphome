# T01 — Repository baseline and recovery record

Recorded 29 September 2026 from `master` at `7cbc7189a84a6f9c3cc52692ef148e1cf2009211`.
This is a **source baseline**, not proof of the firmware currently on either controller.
Keep any exact live YAML, secrets, settings export and firmware backup outside this public repository.

## Sources and identity

| Item | Evidence | Status |
| --- | --- | --- |
| Archived original | `archive/orignial-skink-controller.yaml`, SHA-256 `5c9aeac67ac4f28aef4b11dad2b10bdab8bfdc2b534f0327895307f4398df272` | Public source reference; deployment unconfirmed |
| Shared package | `packages/lumineze-controller.yaml`, SHA-256 `e05c6f467e71256d8c3b572ce32f5db984cc104604d72c3620830518d09faaea` | Current repository implementation |
| Reported new controller | User reported flashing a `my-vivarium` local YAML using the GitHub package on `master`, JungleDawn MAC from a secret, ProT5 omitted | Flash succeeded; exact Git commit, runtime settings and current firmware unconfirmed |
| Archived device identity | `lumineze-controler-skink`, friendly name `LuminEZE Controler Skink`, area `Skink House` | Preserve spelling when migrating that installation |
| Hardware declaration | Generic ESP32-C3, ESP-IDF, two BLE clients | Actual board revision and flash capacity unconfirmed |
| Build environment | Existing CI installs ESPHome 2026.9.0 and generates source | Deployed ESPHome/ESP-IDF versions and compiled size unconfirmed |

The archive and package differ at the device identity, logger/timezone substitutions, local Wi-Fi/API settings, fallback AP settings, MAC substitutions, and explicit lamp-enable queue guard. The 2,300-line control implementation otherwise remains in the shared package; a repository diff is the authoritative exact comparison. Tag `v1.0.0` points at merge commit `1c054c7`; confirm which ref was flashed before using that tag as a recovery source.

## Current code behaviour to preserve or deliberately change

- Lamp index 0 is JungleDawn (`jungle_dawn_client`); index 1 is ProT5 (`prot5_client`). Both clients have `auto_connect: false`. The package's enable flags default to `false`; the shared `queue_lumenize_command` returns before queueing for a disabled lamp. The placeholder MAC for an omitted lamp is `00:00:00:00:00:00`.
- SNTP `controller_time` drives seasonal evaluation; Home Assistant time is also configured and reports sync source. Both use Europe/London in the archive. The package substitutes the SNTP timezone but currently hardcodes Europe/London for Home Assistant time.
- A 10-second interval runs `calculate_solar`; a 1-second interval runs transaction timeout handling and `dispatcher_tick`. There is no explicit `on_boot` automation. Transaction timeouts and retry delays use `millis()`, independent of simulated date/time.
- `calculate_solar` handles real or simulated time, invalid-time fail-safe requests, seasonal targets and automatic queue decisions. `queue_lumenize_command` clamps levels to 0–100 and the lamp maximum, coalesces a latest target and sets pending state. `dispatcher_tick` chooses one due lamp with inter-lamp spacing. Lamp-specific transaction scripts connect, write, request status, wait for readback and disconnect. `record_ble_failure` applies bounded retries and records faults.
- `lamp_target` is the latest requested, capped target; `lamp_inflight` is the sent transaction target; `lamp_last_completed` records a completed write; `lamp_last_reported` comes from a lamp notification. `lamp_readback_fresh` marks whether the most recent command received a report. A completed transaction without a status response is not confirmation of the physical lamp level.
- Solar test mode and manual overrides reset to off at boot. Invalid-time fail-safe restores, default on. Each automatic-control switch restores, default off. All 53 globals use `restore_value: false`; 22 of 26 numbers restore their values. The four non-restoring numbers are the two test levels and simulated calendar day/time. Live restored values have not been captured.
- The archive has 16 binary sensors, 6 switches, 26 numbers, 29 sensors, 19 text sensors, 4 buttons, 6 scripts, 2 BLE clients and 2 intervals. Preserve IDs, entity names, restore settings and timing during mechanical extraction; compare resolved configs, not just source text.

## Baseline cases for later comparison

These are required observations, **not measured outputs**. Capture the current target, queued target, last completed value, lamp report/freshness and status text for each enabled lamp before claiming behavioural parity.

| Input case | Expected baseline evidence |
| --- | --- |
| Night and pre-dawn | Both calculated targets, UVB window status and pending commands |
| Dawn, midday and dusk | Seasonal curve fraction, effective peak, each capped output and threshold behaviour |
| Winter and summer extremes | Seasonal peak scaling and ProT5 calibrated maximum |
| Year boundary and leap day | Calendar-day and effective-day calculations, sunrise/sunset |
| Invalid clock at boot and after grace period | Fail-safe request/retry status and actual readback; do not infer lamp-off from a queued request |
| Manual override during a pending transaction | Newest target, in-flight completion and next dispatch |
| BLE disconnect or no readback | Retry count, communication fault and stale-report indication |

## Private backup and recovery checklist

Before changing a live controller, save privately: (1) its exact local YAML and any local includes, (2) referenced secrets and both real lamp MACs, (3) screenshots/export of restored numbers and switches, (4) installed ESPHome and framework versions plus build logs, (5) the current binary if available, and (6) the known-working USB/serial or OTA recovery route. Keep the backup and credentials out of Git and CI artifacts. A source rollback can use the verified Git ref plus that private configuration; whether the device can actually be recovered by OTA or USB remains to be demonstrated.

## Open evidence

- Which exact YAML/ref is currently deployed on each controller, and whether local edits differ from the repository.
- Actual board/flash variant, installed ESPHome/ESP-IDF versions, binary size, free heap, uptime and BLE connection observations.
- Current persisted control settings and measured outputs for the cases above.
- A private recovery backup and tested physical flash/recovery method; spare-controller availability.

No credential values, real MAC addresses or compiled firmware are included in this record.
