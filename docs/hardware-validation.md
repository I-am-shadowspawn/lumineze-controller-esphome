# T15 bench protocol — draft awaiting measured resource floors

This protocol is for the established Pi Hut ESP32-C3 and physical LuminEZE
JungleDawn/ProT5 lamps. It is a recording template, not hardware acceptance.
Gate A and T23 evidence can be reused only where the exact firmware SHA,
topology, lamps and observations still apply. Do not flash a live vivarium as an
unattended test. Save a known-good USB recovery image and private settings
first. Three/four-fixture layouts remain experimental.

## Freeze before the first candidate run

Record: board and flash/partition revisions; lamp models/firmware and MAC map
(redacted in public evidence); Git SHA; package/component refs; profile;
ESPHome/ESP-IDF versions; topology IDs, roles and slots; timezone; calibration;
HA version; BLE retry/spacing settings; power supply; logging/instrumentation
method; sample cadence; and recovery route. Record the exact candidate image
hash. Stop a run after any firmware/config change and start a new observation
window for affected cases.

| Budget | Predeclared criterion | Status |
| --- | --- | --- |
| Static OTA application size | At most 85% of the **measured actual OTA app partition** for each profile; report image bytes and partition bytes | Proposed; confirm partition on board |
| Free heap and largest contiguous block | Numeric minima derived from measured peak BLE/API/OTA demand plus an explicit reserve | **Unresolved** until instrumented baseline; blocks T15.1 acceptance |
| Policy response | A valid changed demand is evaluated within one normal 10-second tick, barring documented mode gates | Proposed; capture timestamped trace |
| Physical delivery | Within configured dispatcher, connection, transaction and bounded retry windows; no promise of instantaneous output | Proposed; capture write/readback timestamps |
| Stability | No unexplained reset/watchdog, allocation failure, wrong-lamp write, obsolete target revival or unsafe nonzero output | Required stop condition |

The static criterion is a headroom proposal, not proof of runtime memory or OTA
success. Before testing, instrument free heap and largest free block at boot,
BLE connect, write, readback, reconnect, HA traffic, and OTA preparation. Use
those measurements to freeze numeric runtime floors **before** judging the
candidate. Report minimum, maximum and worst transient, not only an average.
Do not lower a floor after a failure without a separately reviewed protocol
revision and a new run.

## Test sequence and evidence IDs

For each of seasonal production/development and schedule
production/development, capture one 24-hour normal run and a separate one-hour
fault/reconnect/OTA exercise. Perform at least 20 reconnect cycles. Record
timestamps, requested/pending/in-flight/completed/reported levels, readback
freshness, retries, group delivery, clock validity, HA state, free heap,
largest block, Wi-Fi/BLE status and reset reason. Retain raw trace privately;
publish a redacted event table and exact source/image hashes.

| ID | Action and expected evidence |
| --- | --- |
| H01 | Boot with automatic off. Verify topology and product assignment, ProT5 maximum 0, time readiness and actual lamp state. |
| H02 | Per-lamp low, medium, high and off manual requests. Confirm BLE readback and physical output, including unreachable-lamp unknown state. |
| H03 | Reduce maximum while output is higher; switch manual/automatic and group controls; verify revoked pending targets and bounded in-flight completion. |
| H04 | Partial group delivery, stale/mismatched/missing readback, disconnect/reconnect and healthy-member progress; verify faults, retry bounds and no stale confirmation. |
| H05 | Power-cycle controller and lamps, lose/recover Wi-Fi, HA and clock; verify default-off and safety behavior, autonomous operation and recovery. |
| H06 | Seasonal representative day/date/peak cases and T23 daily-max/fixed-level sequences, only on a candidate whose T23 capability is advertised. |
| H07 | Schedule step/linear point, midnight wrap, edit/Apply/reject/Cancel, invalid or unconfigured start, DST and reboot persistence against independent T10 expectations. |
| H08 | Development simulation with bench output authorization off/on; verify reset-off and absence of simulation/test entities in production. |
| H09 | Observe all four profile image/partition sizes, heap/fragmentation, API/BLE responsiveness, reset/watchdog and OTA success over the defined windows. |
| H10 | Upgrade v1→generic, same-profile and seasonal↔schedule; compare calibration, schedule/seasonal settings, HA entities and automations. Exercise fixture-assignment fingerprint and interrupted preference writes. |
| H11 | Restore saved previous pinned firmware and private settings by USB; verify lamp identity, readback and autonomous operation afterward. |

Repeat affected cases for shared-code changes. Do not infer a combined-engine
resource budget from separate profile builds. For each profile, record PASS,
FAIL or NOT RUN for every applicable ID, with a trace reference and an explicit
reason for any non-applicable case. The public report must not contain private
credentials, real MACs, or a device-specific firmware binary.

## Stop and recovery

Stop immediately for unexpected nonzero output, wrong lamp assignment,
unbounded retry, stale target revival, unexplained reset, or resource-budget
breach. Use the lamp's physical power control if the BLE state is unknown;
restore the saved bench image and settings by USB. Log the incident and run a
new full affected window after a fix. Completion requires actual device
observations and the numeric resource floors above; a compile or upload is
insufficient.
