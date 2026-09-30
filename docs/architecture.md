# T03 — Ownership map and control contract

For the planned removal of product-specific physical slots, read the
[fixture/group architecture](plans/fixture-topology-architecture.md) and
[T05R/T06R execution runbook](plans/fixture-topology-implementation.md).
They supersede this document's fixed two-slot assumptions for future work.
The description below remains the existing T05/T06 checkpoint, not the new implementation.

Design checkpoint written against the monolithic `packages/lumineze-controller.yaml` at source baseline `7cbc718`. T05 mechanically separated it as recorded in `docs/t05-extraction.md`. T06 implemented the shared control boundary in `core/control.yaml`; the current policy, deviations and evidence are recorded in `docs/t06-control-policy.md`. The implementation uses **parameterised ESPHome scripts plus explicitly owned globals**. A generic C++ framework is unnecessary for two fixed lamp slots.

## Ownership map

| Owner / module | YAML sections and IDs owned | Cross-module interface |
| --- | --- | --- |
| Platform (`core/base.yaml`) | `esphome`, `esp32`, `logger`, `api`, `ota`, shared `wifi` defaults and common substitutions | Supplies platform/network services; local YAML supplies identity, credentials, optional fallback `wifi.ap` and `captive_portal` |
| Time/input (`core/time.yaml`, later `inputs/`) | Both `time` entries, `controller_time`, `homeassistant_time`, `controller_last_time_source`; production clock snapshot | Supplies one coherent evaluation snapshot to an engine. Home Assistant sync text is diagnostic and must not imply that the seasonal engine currently reads the HA clock. |
| BLE transport (`core/ble.yaml`, `lamps/`) | `esp32_ble`, `esp32_ble_tracker`, both `ble_client` entries and callbacks, `jungle_dawn_client`, `prot5_client`, notification sensors `jungle_dawn_status_notification`, `prot5_status_notification`; fixed service/characteristic UUIDs and wire bytes in transaction scripts | Accepts a dispatcher-selected lamp and level; reports connection/readback events. Only this layer refers to BLE client IDs. |
| Dispatcher (`core/dispatcher.yaml`, `lamps/protocol.yaml`) | `queue_lumenize_command`, `record_ble_failure`, `dispatcher_tick`, `jungle_dawn_transaction`, `prot5_transaction`; 1-second timeout/dispatch interval; retry/spacing/timeout numbers | Accepts final authorised target per lamp, serialises transactions, exposes requested/in-flight/completed/reported state. Wire steps and BLE client IDs remain in `lamps/protocol.yaml`. |
| Common control and safety (`core/control.yaml`, `core/controls.yaml`) | `submit_control_target`, `apply_control_policy`; automatic/manual/fail-safe switches, maximum-brightness numbers, invalid-time grace, safe-off/cancel buttons and enable flags | Arbitrates engine/manual/safety requests, applies calibration/limits once, calls the queue. T20 will add an explicit commissioning gate beyond current enable flags. |
| Seasonal engine (`modes/seasonal.yaml`) | `calculate_solar` arithmetic, `solar_*` globals and numbers, `jungle_dawn_curve_*`, `prot5_window_*`, `prot5_curve_*`, mode-specific status and curve sensors | Currently reads the controller clock and publishes desired fractions, peak fractions, validity and simulation flag. T07 will supply an input snapshot. It does not call BLE clients or inspect queue internals. |
| Development input and controls (`inputs/development.yaml`, `features/test-*.yaml`) | `solar_test_mode`, `solar_test_calendar_day`, `solar_test_time_minutes`, `jungle_dawn_test_level`, `prot5_test_level`, manual queue buttons used as test controls | Supplies simulated snapshot or deliberate test request only in development profiles. T07 decides whether simulated inputs can reach lamps. |
| Production diagnostics (`features/diagnostics.yaml`) | Common non-notification `binary_sensor`, `sensor`, `text_sensor` entries for connection, pending, faults, levels, readback, clock and last events | Reads shared state; never owns the transaction or reinterprets a requested level as lamp confirmation. Verbose seasonal calculations move with the engine or to development diagnostics in T08. |

### Explicit state inventory

Every current `globals` ID has one owner:

- **Dispatcher:** `lamp_target`, `lamp_inflight`, `lamp_last_completed`, `lamp_last_reported`, `lamp_readback_received`, `lamp_readback_fresh`, `lamp_pending`, `lamp_request_generation`, `lamp_inflight_generation`, `lamp_connected`, `lamp_ever_attempted`, `lamp_last_attempt_ms`, `lamp_last_failure_ms`, `lamp_retry_delay_ms`, `lamp_attempts_for_request`, `lamp_completed_count`, `lamp_failure_count`, `lamp_consecutive_failures`, `transaction_active`, `active_lamp`, `transaction_started_ms`, `transaction_write_completed`, `any_attempted`, `global_last_attempt_ms`, `next_lamp`, `dispatch_choice`.
- **Control/safety:** `invalid_time_failsafe_sent`, `control_target`, `control_should_queue`, `control_invalid_output`, `control_limit_applied`, `automatic_last_queued`, `automatic_has_queued`.
- **Engine contract:** `engine_output_fraction`, `engine_peak_fraction`, `engine_output_valid`, `engine_output_simulated`.
- **Seasonal:** `solar_calculation_valid`, `solar_source_day`, `solar_year_days`, `solar_effective_day`, `solar_declination_degrees`, `solar_day_length_hours`, `solar_sunrise_minutes`, `solar_sunset_minutes`, `solar_elevation_degrees`, `solar_daylight_envelope`, `solar_evaluation_minutes`, `jungle_dawn_curve_fraction`, `jungle_dawn_season_factor`, `jungle_dawn_effective_peak`, `jungle_dawn_calculated_target`, `prot5_window_start_minutes`, `prot5_window_end_minutes`, `prot5_window_length_hours`, `prot5_window_envelope`, `prot5_curve_fraction`, `prot5_effective_peak`, `prot5_calculated_target`.

Other explicit IDs are assigned as follows:

- **Dispatcher settings:** `ble_min_lamp_interval`, `ble_inter_lamp_quiet`, `ble_retry_base_delay`, `ble_max_attempts`, `ble_transaction_timeout`, `automatic_recovery_interval`.
- **Common control settings:** `jungle_dawn_max_brightness`, `prot5_max_brightness`; **seasonal settings:** `solar_simulated_latitude`, `solar_noon_minutes`, `solar_phase_offset_days`, `jungle_dawn_curve_exponent`, `jungle_dawn_winter_peak_scale`, `jungle_dawn_summer_peak_scale`, `jungle_dawn_minimum_automatic_change`, `prot5_start_offset_minutes`, `prot5_end_offset_minutes`, `prot5_curve_exponent`, `prot5_winter_peak_scale`, `prot5_summer_peak_scale`, `prot5_minimum_automatic_change`.
- **Common diagnostics:** `jungle_dawn_connected`, `prot5_connected`, `jungle_dawn_dispatch_status`, `prot5_dispatch_status`, `jungle_dawn_last_completed_time`, `prot5_last_completed_time`, `jungle_dawn_last_reported_time`, `prot5_last_reported_time`, `jungle_dawn_readback_status`, `prot5_readback_status`.
- **Seasonal diagnostics:** `solar_engine_status`, `solar_evaluation_time_text`, `solar_sunrise_text`, `solar_noon_text`, `solar_sunset_text`, `solar_day_length_text`, `jungle_dawn_curve_status`, `prot5_curve_status`, `prot5_window_start_text`, `prot5_window_end_text`.

The `calculate_solar` script still owns seasonal arithmetic, seasonal preview and the current clock read. T06 moved invalid-clock safety, automatic/manual arbitration, limits and queue triggers into common control. T07 will separate its input provider. BLE notification sensors still update dispatcher globals and status text directly; T08 can narrow the diagnostic interface. There is no `on_boot` hook. The 10-second evaluation interval invokes the engine and common policy; the 1-second interval belongs to transaction timeout and dispatch. Each is declared once. The two `on_time_sync` hooks only publish source text today.

Persisted settings have exactly one owner: transport timing/retry numbers belong to dispatcher; invalid-time grace and fail-safe switch to safety; lamp maximums and automatic/manual switches to control; solar latitude, noon, phase, curve/window and seasonal peak settings to seasonal. Development owns all simulated date/time and test levels. Preserve the current ID, entity name, restore flag/default and range while moving each setting. The production set of controls is automatic enable, manual override/level, maximum/calibration, safe-off and bounded transport/safety settings; T07/T08 decide the precise removal of test and verbose controls.

## Proposed evaluation and output contract

One orchestrator takes a snapshot once per 10-second evaluation. The snapshot contains `valid`, actual source/provider, local year, day-of-year, days-in-year (365/366), local minutes since midnight including seconds as a fraction, and whether the input is simulated. It is immutable for that evaluation. Invalid/non-finite values make the snapshot invalid; the engine does not read `controller_time` or test entities directly. The real provider uses the controller's configured timezone. Transaction, retry and grace timers continue to use monotonic `millis()`; a simulated day or clock correction cannot accelerate them.

The current seasonal engine produces validity, desired and peak fractions for slot 0 (JungleDawn) and slot 1 (ProT5), plus a simulated-input flag. Fractions are expected to be finite and in `[0, 1]`: 0 means off; 1 means 100% of that lamp's configured maximum. Seasonal scale and curve shape are engine-owned; the daily schedule will convert its configured percent to a fraction. The engine does not see BLE IDs, transaction state or lamp MACs. Common control rejects invalid or non-finite engine output and holds the current target. T07 will add the coherent input snapshot described above.

Common control converts an authorised fraction to lamp percent **once** using `std::lround(maximum_percent * fraction)` and clamps the result to `[0, 100]`. Manual input is an integer percent and passes through the same maximum cap. ProT5's calibrated maximum of zero produces zero. The queue receives only a final integer percent and does no engine-specific arithmetic or cap calculation. The seasonal preview still calculates the historic target for display, while common control owns the operational target.

Priority per lamp is: (1) disabled lamp: no operational queueing; (2) invalid-clock safe-off after its grace period; (3) explicit safe-off; (4) active manual override/latest manual request; (5) automatic request if enabled and engine valid; (6) hold current request. Explicit safe-off is a 0% request, not a persistent latch: it remains in effect while controls stay off, and a deliberate manual request or automatic re-enable supersedes it on the next policy evaluation. Active invalid-clock safety cannot be superseded. Switching automatic off holds state rather than sending zero. A new target during an in-flight write waits for that transaction to finish. Request generations prevent a cancelled target from being resurrected by the older completion or failure. T06's simulated transport scenarios exercise this path; physical-lamp observation remains open.

The shared state names mean different things: **requested** is the latest authorised final target; **pending** means it awaits dispatch/retry; **in-flight** is the target copied when a transaction starts; **completed** means the transaction write path finished; **reported** is the last valid lamp notification, with freshness tied to the last command. A missing/stale report is unknown physical output, even after a successful write or safe-off request. Diagnostics expose these separately.

## Verification and open policy decisions

- T05 extraction must preserve a resolved-config inventory: one owner for each ID, two BLE clients, one 10-second evaluation and one 1-second dispatch interval, no duplicate callbacks, unchanged entity names and restore settings.
- T06's implemented policy and simulated transport evidence are in `docs/t06-control-policy.md`. Physical-lamp observations and real recovery validation remain open.
- T07 settles whether simulation may drive physical lamps and removes development IDs from production builds. T08 chooses the production diagnostic subset. T10 specifies schedule time/DST semantics.
- T01's field observations remain open. Neither this design nor a firmware compile proves the hardware behaves as intended.
