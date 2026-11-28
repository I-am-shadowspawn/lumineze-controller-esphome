# T19 — Implement and test generic provisioning firmware

**Depends on:** T18 design approved.  
**Intent:** provide a credential-free initial firmware that provisions Wi-Fi and
OTA/API access, then hands off to a full profile.

**Status (in repo):** T19.1 is complete — `firmware/bootstrap.yaml` and
`ci/bootstrap.yaml` validate and compile on ESPHome 2026.11.0 / ESP-IDF 5.5.6,
with isolation, identity and dummy-boundary checks enforced by
`scripts/check_bootstrap_isolation.py`; sizes recorded in
`docs/evidence/t19-t22-software.md`. T19.2–T19.5 require a board.

## Decisions already settled by T18

- Use a **minimal bootstrap** (`firmware/bootstrap.yaml`) with no BLE lamp transport.
- First provisioning uses **Improv Serial** and **captive portal** over USB.
- BLE Improv is deferred until T21/T22 prove coexistence.
- Bootstrap is profile-agnostic; profile selection happens in the generated local YAML.
- Project identity is included; `controller_profile: bootstrap`.

## Remaining work

### T19.1 — Bootstrap firmware compile and size check

- Validate and compile `firmware/bootstrap.yaml` on the supported toolchain
  (ESPHome 2026.11.0 / ESP-IDF 5.5.6, ESP32-C3).
- Ensure it compiles with `ci/bootstrap.yaml` and with a Device-Builder-style
  consumer wrapper using remote package refs.
- Record RAM/flash size and confirm it is smaller than the full profiles.

### T19.2 — First-boot access point behavior

- Erase or flash a fresh board.
- Confirm it starts the setup AP when no Wi-Fi is configured.
- Confirm the SSID uses the configured friendly name and does not leak secrets.

### T19.3 — Improv Serial and captive portal provisioning

- Provision Wi-Fi via Improv Serial and/or captive portal.
- Confirm the board connects and shows online in Home Assistant / ESPHome Device Builder.
- Test wrong password handling and recovery.

### T19.4 — Credential retention and reboot

- Reboot the provisioned board.
- Confirm Wi-Fi, API and OTA credentials persist.
- Confirm the commissioning switch remains off and the status sensor reports
  uncommissioned.

### T19.5 — Two-board independence test

- Repeat T19.2–T19.4 on a second board.
- Confirm each board has unique identity and does not share credentials.
- Confirm neither board can transmit operational lamp commands (no BLE
  transport, no fixtures).

### T19.6 — Handoff to T20

- Document bootstrap evidence, including commands, observed SSIDs, sizes and
  any anomalies.
- Update `ci/profile-matrix.json` if additional checks are required.

## Acceptance criteria

- `firmware/bootstrap.yaml` compiles and passes CI identity checks.
- A fresh board can be provisioned without copying controller logic.
- No operational lamp command is possible from the bootstrap firmware.
- Recovery path is documented.

## Exit condition

T19 is complete when bootstrap hardware behavior is recorded and the next step
(T20 adoption) can begin.
