# Upgrade, profile switch, and recovery

Keep a copy of the current private YAML and `secrets.yaml`, the exact package
and component Git refs, a known-working firmware binary or USB recovery route,
and a Home Assistant settings/entity inventory **before** changing firmware.
Store this outside the public repository. Record actual reported lamp levels
and physical off observations before making changes. Treat each profile or
topology switch as a controlled recommissioning, not a settings migration.

## v1 two-product controller to generic topology

The legacy `packages/lumineze-controller.yaml` adapter remains available, and
`example/vivarium-example.yaml` points to immutable `v1.0.0` for recovery.
Build the new generic wrapper separately. Map the installation deliberately:

| Existing v1 value/control | Generic destination |
| --- | --- |
| Controller name, area, Wi-Fi, API and OTA secrets | Local wrapper and private `secrets.yaml`; preserve or rotate intentionally |
| JungleDawn MAC and enable flag | One `type: jungle_dawn` visible fixture descriptor and matching package fragment |
| ProT5 MAC and enable flag | One `type: prot5` UV fixture descriptor and matching package fragment; leave maximum at 0 until checked |
| Lamp order / implicit slots | Explicit unique slots 0–3; choose and record them, without assigning product meaning |
| Shared latitude, noon, phase and visible/UV seasonal peaks | Selected `context-seasonal.yaml` context, entered and verified in HA |
| Per-lamp automatic and manual settings | Visible/UV group switches and named fixture controls; leave automatic off until recommissioned |
| Per-lamp maximum and minimum change | Named fixture controls; re-enter and verify physically |
| Existing HA entity IDs and automations | Inventory, then update references to the new context/group/fixture entities |

Capture the old values by screenshot or export and compare them after setup.
The generic layout does **not** promise that v1 preferences, calibration keys,
entities, or HA automations migrate. A new ProT5 remains limited to 0% until
explicit calibration. Run the complete low/off and readback checks in
[installation](installation.md) before enabling automatic output.

## Seasonal and schedule switches

Choose the new profile in YAML; runtime Home Assistant actions cannot switch
engines. Preserve the original wrapper and settings capture. For
seasonal→schedule, record seasonal context values, group and fixture settings,
then define complete visible/UV point sets for every used role, Apply, and
verify the active revision before automatic enable. For schedule→seasonal,
record active points, interpolation and revision, then enter seasonal location,
noon, phase and role curves. There is no defined conversion between a solar
curve and a daily point schedule. T23 temporary controls are seasonal-only and
are not restored in schedule firmware. Both directions require a fresh check
of calibration, grouped output, BLE readback and HA automations.

Schedule preference identity depends on context ID and its used-role mask.
Changing either creates a new schedule namespace; re-enter all points and
Apply. Fixture calibration identity depends on fixture ID, slot, product and
MAC, so changing any of these requires calibration again. Display labels and
HA entity IDs may change independently of firmware storage. A successful
compile does not prove settings survived a switch; T15 must verify persistence
on the actual board.

## Development to production

Development profiles include simulation and preview controls. Record test
settings for the bench record, then choose the matching production package
and `input_provider: real`. Remove the development fragment for each fixture.
Simulation enable and output authorization are non-restoring, and production
omits those entities. Remove or update any HA dashboards and automations that
refer to development-only entities. Verify that actual time is valid and
automatic controls are still off before enabling groups. Returning to
development also starts simulation disabled; do not expect test state to
reappear.

## Pinned rollback

If the new build or behavior fails, turn off group automatic/manual controls
and use confirmed physical lamp power controls where necessary. Restore the
saved private YAML and **both** matching immutable package/component refs, or
flash the saved known-working binary by USB. Reconnect HA and check real BLE
readback and physical lamp state before resuming automation. Do not merely
change `controller_ref` to a floating branch or assume an older engine can
interpret newer preferences. Restore settings manually from the saved
inventory, checking entity IDs and HA automations. Rollback success requires
an observed working controller and lamp state; loading old YAML alone is not
confirmation.

Current compatibility boundaries and the candidate identity are in
[compatibility](compatibility.md). Gate A, T13.4 and T15 physical upgrade and
retention evidence remain open.
