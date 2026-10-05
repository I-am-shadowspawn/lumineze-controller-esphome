# LuminEZE vivarium light controller

This project provides reusable ESPHome firmware for controlling LuminEZE
JungleDawn and ProT5 lights over Bluetooth Low Energy (BLE). It connects the
lights to Home Assistant over Wi-Fi, where you can set seasonal schedules,
automatic and manual levels, fixture calibration, and diagnostics.

The established hardware platform for this project is [The Pi Hut Bluetooth
Proxy for Home Assistant](https://thepihut.com/products/bluetooth-proxy-for-home-assistant),
which uses an **ESP32-C3**. Its USB connection is used to install firmware and
power the controller. The Pi Hut's [hardware setup guide](https://thepihut.com/blogs/raspberry-pi-tutorials/bt-proxy-user-guide)
covers the board and its initial USB installation.

When this project's firmware is installed, the board acts as a dedicated
LuminEZE light controller. It does not run ESPHome's general-purpose Bluetooth
Proxy service at the same time. Home Assistant communicates with the controller
through the ESPHome integration; the controller communicates with each lamp
directly over BLE.

## Before you start

This is a configurable ESPHome project, rather than a one-click lamp pairing
app. You do not need to write C++, but you should be comfortable editing a
small YAML file and following setup or compile messages.

### Knowledge you will need

- **Home Assistant:** open its settings, install or use ESPHome Device Builder,
  add an ESPHome device, and find the device's entities after it connects.
- **ESPHome and YAML basics:** edit names and values while preserving YAML
  indentation; understand that `!secret` reads a private value and that
  `packages` imports reusable configuration from this GitHub repository. See
  the [ESPHome packages guide](https://esphome.io/components/packages/).
- **Your Wi-Fi details:** the network name and password that the controller
  should use. The controller and Home Assistant need network connectivity to
  communicate.
- **BLE lamp identity:** find the Bluetooth MAC address for each LuminEZE lamp
  and match it to the physical fixture you intend to control. A lamp's MAC is
  not the ESP32 board's address.
- **Light calibration:** choose each lamp's calibrated maximum and understand
  that automatic/group levels use that calibration. ProT5 starts at a 0%
  maximum as a safety measure.
- **Basic commissioning:** understand that a requested level, a completed BLE
  write, and a lamp's reported level are separate pieces of information. An
  “off” request cannot confirm that an unreachable lamp is physically off.

### Hardware, software and private values to have ready

- The Pi Hut ESP32-C3 Bluetooth Proxy board, its USB-A connection, and a data
  capable USB port/cable on a computer for first installation. The board can
  then be powered from a suitable USB supply near the vivarium.
- A working Home Assistant system with ESPHome Device Builder available, plus a
  browser/computer that can access Home Assistant. Initial USB flashing is
  simplest with the board connected to that computer; see the Pi Hut guide for
  browser and USB flasher requirements.
- Reliable Wi-Fi coverage where the controller will be installed and the Wi-Fi
  SSID/password.
- The BLE MAC address of each lamp, a device name and area name, and the
  controller's Home Assistant API encryption key.
- A private ESPHome `secrets.yaml` containing Wi-Fi credentials, the API key,
  and lamp MAC addresses. The generic example expects `wifi_ssid`,
  `wifi_password`, `my_vivarium_encryption_key`,
  `my_vivarium_jungle_dawn_mac`, and `my_vivarium_prot5_mac`. The legacy
  example uses the names in [`example/secrets-example.yaml`](example/secrets-example.yaml).
  Never commit real secrets, MAC addresses, or a completed local device YAML
  to this public repository.

The ESPHome API encryption key must be a valid 32-byte base64 key. One way to
generate one on a computer with OpenSSL is `openssl rand -base64 32`; put the
result in the matching private secret. Do not use an example placeholder.

## Choose the configuration

There are two package paths:

| Use this when… | Configuration |
| --- | --- |
| You already run the v1 two-product controller and want to keep its existing configuration and Home Assistant entity IDs | [`packages/lumineze-controller.yaml`](packages/lumineze-controller.yaml) |
| You are creating a new controller with explicit fixture identities, slots and control groups | [`example/topology-two-lamps.yaml`](example/topology-two-lamps.yaml), using [`packages/seasonal-production.yaml`](packages/seasonal-production.yaml) |

The matching generic development profile is
[`packages/seasonal-development.yaml`](packages/seasonal-development.yaml).
Both use the same seasonal engine and policy path; only the input provider and
optional development diagnostics differ. See
[`docs/seasonal-profiles.md`](docs/seasonal-profiles.md).

The generic topology is the recommended starting point for a new installation.
Its example defines one seasonal context and two groups: `visible` for
JungleDawn and `uv` for ProT5. Each fixture is named and assigned a slot
explicitly, so the product type does not depend on lamp order. The example
places ProT5 in slot 0 and JungleDawn in slot 1.

The current generic software has been configuration-validated and compiled for
the ESP32-C3, but the generic multi-fixture package has not yet been validated
with physical lamps. Commission it carefully on the actual setup. Three- and
four-fixture topologies are experimental and require explicit opt-in; a
successful compile does not demonstrate reliable operation on hardware.

## First setup with the generic example

1. **Prepare Home Assistant and Device Builder.** If this is a new Pi Hut
   board, first follow the Pi Hut [Bluetooth Proxy hardware guide](https://thepihut.com/blogs/raspberry-pi-tutorials/bt-proxy-user-guide)
   to confirm USB access and open ESPHome Device Builder. You will replace the
   generic proxy firmware with this project's controller firmware.
2. **Copy the example into your ESPHome configuration.** Use
   [`example/topology-two-lamps.yaml`](example/topology-two-lamps.yaml) as the
   starting device YAML. Keep `controller_ref` the same for the remote package
   and external component declarations in that file. `master` follows ongoing
   changes; for a long-lived installation, pin it to a reviewed commit or
   release tag.
3. **Add private secrets.** Add the required key names to your private
   ESPHome `secrets.yaml`. The generic two-lamp example uses the five
   secret names listed above. Set your Wi-Fi values, API encryption key, and
   the MAC for each lamp you will enable. Do not use dummy addresses.
4. **Name and identify your installation.** In the device YAML, set
   `device_name`, `friendly_name`, `area_name`, `timezone`, and the fixture
   IDs/names. Keep IDs stable after installation because they identify Home
   Assistant entities and stored settings.
5. **Review the topology.** For every enabled fixture, make its ID, slot,
   product type, group and MAC agree in both the package list and the
   `lumineze_topology.fixtures` section. Use the documented example as a whole
   before changing its structure. More detail is in the
   [topology controller guide](docs/topology-controller.md).
6. **Validate and install.** Save the YAML, let ESPHome validate and compile
   it, then install over USB for first provisioning. Once online, ESPHome OTA
   can be used for later updates. Confirm that the device is online in
   Home Assistant before setting up light controls.
7. **Commission each lamp.** Verify that each fixture's BLE status and
   diagnostics refer to the intended physical lamp. Set each fixture's
   calibrated maximum; a new ProT5 starts at 0% maximum, so it will not receive
   nonzero UV output until you calibrate it. Group automatic and manual controls
   start off after boot. Enable them deliberately after checking the settings.

For existing installations, do not switch a live v1 controller to the generic
package expecting its old Home Assistant entities or saved settings to migrate
automatically. Export or record the current settings, keep the known-good YAML
and Git ref for recovery, and use the migration notes in the
[topology controller guide](docs/topology-controller.md).

## How the controller is organized

- A **fixture** is one physical LuminEZE lamp. It has its own BLE address,
  calibration, manual control, target, and connection/readback diagnostics.
- A **group** chooses visible or UV output from a seasonal context and applies
  its automatic or group-manual demand to its member fixtures.
- A **context** owns the location and seasonal settings used to calculate
  visible and UV demand. One or two contexts can be configured.
- A **slot** is an explicit controller storage/dispatch position. It does not
  determine lamp type or behavior.

The visible role is currently JungleDawn and the UV role is ProT5. Group manual
levels are percentages of each member's calibrated maximum; fixture manual
levels are absolute lamp percentages, capped at that fixture's maximum. Read
the [controller guide](docs/topology-controller.md) for entity behavior,
calibration identity, migration, diagnostics, and the software/hardware support
boundary.

### Temporary lighting controls

Each fixture also has temporary controls in Home Assistant. **Today's Automatic
Maximum** is an absolute lamp percentage for the current local day; edit its
number and press **Apply Today's Maximum**. The seasonal curve and permanent
calibration remain unchanged. The fixture follows the curve up to that level,
holds there while the curve is higher, then resumes on the first sampled curve
value at or below the maximum during the evening descent. The maximum expires
at the next local date change.

For a timed hold, set **Fixed Level** (0–100%) and **Fixed Duration**
(15 minutes to 24 hours), then press **Start Fixed Level**. That fixture stays
at the selected level, subject to its calibrated maximum, while the seasonal
calculation continues in the background. At expiry, the controller reevaluates
the current curve and resumes from its current level. Use **Cancel Temporary
Lighting** to return early; this can immediately raise the lamp to the current
curve level.

Temporary actions require valid seasonal output and automatic control for the
fixture's group. Manual override, group automatic-off, safe-off, invalid live
time, or controller reboot clears the temporary mode. The temporary status and
remaining-time entities show the controller's decision; use the existing
requested, completed, reported, and readback entities to check what the lamp
actually received.

## Repository map

- [`example/topology-two-lamps.yaml`](example/topology-two-lamps.yaml): generic
  two-lamp Device Builder configuration.
- [`example/vivarium-example.yaml`](example/vivarium-example.yaml): legacy v1
  configuration example.
- [`packages/`](packages/): reusable ESPHome configuration, including the
  legacy package and generic topology fragments.
- [`docs/topology-controller.md`](docs/topology-controller.md): topology
  configuration, behavior, migration, and validation evidence.
- [`docs/diagnostic-profiles.md`](docs/diagnostic-profiles.md): production and
  development diagnostic entities and their update intervals.
- [`docs/seasonal-profiles.md`](docs/seasonal-profiles.md): supported seasonal
  entry points, profile differences, and Gate A evidence.
- [`docs/build.md`](docs/build.md): repository build, secrets, and private
  configuration notes.

For questions or problems, include the board model, ESPHome version, selected
package path, and sanitized validation/log output. Remove Wi-Fi passwords,
encryption keys, real MAC addresses, and private network details before
sharing logs.

## Planned daily schedule mode

The [T10 daily schedule contract](docs/schedule-behaviour.md) defines independent
visible/UV schedules per context, cyclic local-time step or linear interpolation,
and staged Home Assistant settings with explicit Apply/Cancel. Schedule mode is
specified but **not implemented or available to install**. Seasonal profiles
remain the current software entry points; Gate A hardware evidence still gates
schedule implementation. See the [delivery roadmap](docs/plans/t10-t17-delivery-index.md)
for implementation, verification and release tasks.
