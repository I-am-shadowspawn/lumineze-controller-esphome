# Install and commission a generic controller

This is the manual Device Builder route for the Pi Hut ESP32-C3 Bluetooth Proxy
board. It replaces proxy firmware with dedicated LuminEZE firmware. The four
candidate wrappers are software validated; Gate A and T15 physical evidence are
still open. Use a controlled bench setup before relying on automatic output.

## 1. Prepare the private device file

Have Home Assistant, its ESPHome Device Builder, a data-capable USB connection,
reliable 2.4 GHz Wi-Fi, and the actual BLE MAC of each lamp. You need basic YAML
editing and access to the controller's Home Assistant entities. Choose one
wrapper from `example/`:

| Need | Wrapper |
| --- | --- |
| Real time with a seasonal solar curve | `seasonal-production.yaml` |
| Seasonal bench simulation and detailed diagnostics | `seasonal-development.yaml` |
| Real time with an editable daily schedule | `schedule-production.yaml` |
| Schedule bench simulation and detailed diagnostics | `schedule-development.yaml` |

Copy the chosen file into your **private ESPHome configuration**. Keep the
package and external-component refs on the same full immutable SHA. Set a
unique `device_name`, friendly name, area, and IANA `timezone`. Verify each
fixture's ID, product, slot, group, and MAC in both its package fragment and
the `lumineze_topology.fixtures` descriptor. Slot numbers are arbitrary; this
example places ProT5 in slot 0. Add/remove the corresponding fragment and
descriptor together. The [wrapper contract](installation-contract.md) gives
the limits and rules. Do not publish the completed file with real MACs.

In the same private ESPHome directory, create `secrets.yaml` with
`wifi_ssid`, `wifi_password`, `my_vivarium_prot5_mac`,
`my_vivarium_jungle_dawn_mac`, and `my_vivarium_encryption_key` (rename keys
consistently if you change the wrapper). Generate a **unique** API encryption
key with `openssl rand -base64 32`; the illustrative values in
`example/secrets-example.yaml` are not installation credentials. Add a private
OTA password if your site requires one. Keep secrets, expanded configs, build
logs and firmware binaries out of the public repository.

## 2. Validate and install

In Device Builder, save the private YAML and run **Validate**. Resolve schema,
missing secret, duplicate ID, wrong MAC, and package-ref errors before
compiling. Run **Install** to compile, then install by USB for first provision
using the Device Builder/Pi Hut board guide for your host. A successful compile
or upload proves neither lamp identity nor BLE control. On later updates, OTA
is suitable only after the device is online and the pinned rollback file is
retained. Do not change engine or topology through an OTA update without the
recommissioning steps below.

Confirm the controller appears online in Home Assistant's ESPHome integration.
Record the board/ESPHome/build-profile/source-revision diagnostics, device
name, and the entity IDs used by any automations. The project version
`2.0.0-dev` identifies an unreleased candidate, not physical acceptance.

## 3. Commission physical lamps

Group Automatic Control and Manual Override start **off** after boot. Keep
them off while confirming that each displayed fixture matches the intended
physical lamp and its BLE MAC. A new ProT5 has calibrated maximum **0%**;
leave it there until its placement and safe operating level have been checked.
Confirm the visible/UV group assignment and each fixture's reported state.

For each lamp in a controlled environment, set a conservative calibrated
maximum, request a low manual level, then request off. Check the physical lamp
and the fixture's requested, completed, reported, readback-fresh, retry/fault,
and group-delivery diagnostics. A requested 0%, completed write or a stale
report is **not** physical off confirmation. If a lamp is unreachable, stop
commissioning and use its own safe physical power control; do not infer its
state from the controller. Only after the correct lamps respond and off is
confirmed should you enable Automatic Control for the intended groups.

For a **seasonal** profile, set latitude, local solar noon, season phase and
role peaks/curves in Home Assistant before enabling automatic. Check the
context's valid-time/evaluation status and current demand. Temporary lighting
is a seasonal-only capability: stage Today's Automatic Maximum then Apply, or
stage Fixed Level and a 15-minute-step duration then Start Fixed Level. Inspect
the temporary status and actual BLE readback; Cancel may immediately resume a
higher current curve level. These controls are unavailable in schedule builds.

For a **schedule** profile, each used visible/UV role has an interpolation mode
and eight editable point slots. Enter at least two enabled points per used role
with unique integer local minutes 0–1439 and integer levels 0–100. Press
**Apply Schedule** for each context; editing alone leaves the active schedule
running. Inspect Active Schedule Valid, Active Schedule Revision, Schedule Edits
Pending and Schedule Status. A rejected Apply identifies the role/point and
leaves the prior active revision intact; correct the draft or press **Cancel
Schedule Edits**. Cancel reloads the active values and does not send a lamp
command. Confirm the schedule output and low/off readback before enabling the
group. The [schedule behavior contract](schedule-behaviour.md) defines midnight
and interpolation details.

## 4. Capture the installation result

Keep a private record of the wrapper, SHA, firmware binary or recovery path,
MAC-to-lamp map, calibration, schedule/seasonal settings, entity IDs and any HA
automations. Record physical observations separately from validation, upload
and requested values. The [upgrade and recovery guide](upgrade-recovery.md)
covers profile changes and rollback. Bench acceptance belongs to
`docs/plans/t15-bench-acceptance.md`; this guide does not close that gate.
