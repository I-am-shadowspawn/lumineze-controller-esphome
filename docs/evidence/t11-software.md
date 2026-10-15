# T11 software acceptance — 5 October 2026

Branch `implementation/t11-t17`; engine implementation through `931d7e7`.
ESPHome 2026.9.0, ESP32-C3, ESP-IDF 5.5.5. Dummy CI MACs/network only.
Owner authorized isolated software work with hardware gates open.

## Current-source full builds

| Profile | Fixture | Static RAM bytes | Flash bytes |
| --- | --- | ---: | ---: |
| Seasonal production | `ci/topology-generic.yaml` | 147152 | 1258710 |
| Seasonal development | `ci/topology-generic-development.yaml` | 147984 | 1272090 |
| Schedule production | `ci/schedule-generic.yaml` | 147792 | 1254672 |
| Schedule development | `ci/schedule-generic-development.yaml` | 148616 | 1268122 |

Commands: `esphome compile <fixture>` using the pinned environment and separate
build directories. Logs: `/tmp/t11-final-seasonal{,-dev}-build.log` and
`/tmp/t11-schedule{,-dev}-isolation-build.log`. CI must reproduce this evidence;
local temporary logs are not permanent release artifacts. Linker RAM is not
runtime heap headroom. The schedule storage working-set assertion is <=1 KiB;
HA entity/framework overhead is additional and awaits bench measurement.

## Contract coverage

- 56 numerical outputs, 22 staged validations and eight calibrated conversions:
  `python scripts/check_schedule_cases.py`.
- All 21 T10 control/HA scenario IDs: `python scripts/check_schedule_policy.py`.
  Executes production schedule and policy lambdas, including safe-off. HA network
  loss is modeled as absence of any HA input; actual HA editing remains a bench test.
- All 13 persistence scenarios: `python scripts/check_schedule_storage.py`.
  Independent CRC, every single-byte corruption and all 88 torn-write prefixes,
  modulo rollover/ambiguity and uncertain flush/readback locking are exercised.
- Actual Apply/Cancel action lambdas: `python scripts/check_schedule_editor.py`.
- Real ESPHome schema and failure cases: `python scripts/check_schedule_schema.py
  esphome`, existing `check_topology_schema.py`, and ten schedule compositions via
  `check_topology_matrix.py --schedule esphome` (config validation, not full builds).
- All four generated sources: `check_profile_isolation.py`; seasonal resolved
  entity/default/restore inventory: `check_seasonal_inventory.py esphome`.
- Existing fixture conversion, transport, protocol trace, safe-off, timeout, T23
  policy, 1,600 seasonal oracle comparisons and seasonal provider parity pass.

## Required physical handoff

Gate A and T23 acceptance remain pending. T15 must capture operator, immutable
SHA, board/lamp versions and sanitized traces for:

1. Real HA editor Apply/Cancel/rejection and all used roles; fresh boot defaults.
2. Durable Apply followed by reboot/power interruption, corrupted-bank recovery
   and profile/firmware upgrade/rollback with actual retained values.
3. Step/linear boundaries and daily wrap; clock loss/recovery and skipped points.
4. Apply during BLE connect/write/readback; unchanged target with obsolete write;
   requested/completed/reported freshness and unreachable lamp recovery.
5. Manual, automatic-off and safe-off priority; calibration reduction and ProT5
   zero default; shared/independent groups and controller-specific MAC mapping.
6. Development calculation-only and explicit bench gate, then production removal
   of simulation controls; seasonal T23 sequences without regressions.
7. Long-running free/minimum heap, Wi-Fi/BLE load and HA reporting at maximum
   editor topology. Three/four fixtures remain experimental until measured.

No live device was flashed. No physical outcome, stable release or migration is
claimed by these host/build results.
