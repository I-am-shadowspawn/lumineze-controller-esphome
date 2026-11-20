# T13 software identity checkpoint — 7 October 2026

`shadowspawn.lumineze` / `2.0.0-dev` is an **unreleased** project identity.
All four generic profiles and both legacy compatibility fixtures compile on
ESPHome 2026.9.0 (ESP-IDF 5.5.5 on ESP32-C3). Four generic build summaries at
source `a14c958c63891fd8e06b75a9b1d287b7bc165fcf` show:

| Profile | Static RAM bytes | Flash bytes |
| --- | ---: | ---: |
| Seasonal production | 147416 | 1260284 |
| Seasonal development | 148248 | 1273488 |
| Schedule production | 148064 | 1256200 |
| Schedule development | 148888 | 1269660 |

Legacy compatibility production/development also compile: 148180/1427440 and
149932/1445084 RAM/flash bytes respectively. The six resolved/compiled metadata
checks pass, and generic generated source shows the exact SHA, with no dirty
firmware assets at that build. Legacy source reference is explicitly unverified.
Logs are `/tmp/t13-*-build.log`; CI will produce retained summaries for the
candidate commit. A later docs commit does not make this earlier binary a new SHA.

The metadata fragment has no `on_update` action. Its four diagnostics are
read-only. Resolved generic group automatic/manual and fixture manual switches
remain `ALWAYS_OFF`. Existing seasonal entities/defaults/restore values still
match the pre-T11 inventory beyond these four additions. Host tests cover
schedule persistence and assignment-bound fixture calibration separately.

**Physical evidence pending:** HA/device information must display the expected
project, profile, ESPHome and source values on each installed board. For a real
upgrade, record previous/new HA entities, schedule revision/points, calibration,
automatic-off state and rollback results. Confirm stored values after power loss
and OTA/USB recovery. Static RAM is not minimum runtime heap. T13.4 and T15 stay
open until these observations are captured with board, lamp and firmware SHA.
