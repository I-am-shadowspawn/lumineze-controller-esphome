# T22 — Rehearse a fresh installation and release the adoption workflow

**Depends on:** T21 CI checks passing.  
**Intent:** confirm the documented experience works for someone who did not build the
package internals.

## Decisions already settled by T18–T21

- Bootstrap firmware is flashed over USB; it has no lamp transport.
- Adoption uses ESPHome Device Builder with `dashboard_import` and `import_full_config: false`.
- The generated local wrapper selects one of the four profiles and supplies real fixture MACs.
- Commissioning is explicit via `topology_commissioned`.
- CI validates bootstrap isolation and adopted example consistency.

## Remaining work

### T22.1 — Prepare a blank board

- Use a compatible ESP32-C3 board that has not been provisioned for this project.
- Flash the bootstrap firmware from `example/bootstrap.yaml` over USB using the
  documented SHA pin.

### T22.2 — Provision Wi-Fi

- Confirm the setup AP appears.
- Connect via captive portal or Improv Serial and supply the target Wi-Fi credentials.
- Confirm the board is online in Home Assistant / ESPHome Device Builder.

### T22.3 — Adopt in Device Builder

- Use the `dashboard_import` URL from `adopt/lumineze.yaml`.
- Inspect the generated YAML; confirm it imports `adopt/lumineze.yaml` and no
  `import_full_config: true`.
- Edit the generated YAML to select a production profile and supply fixture MACs.
- Validate and install the adopted profile.

### T22.4 — Commission and verify

- Confirm `topology_commissioned` is off after first boot.
- Confirm the controller does not connect to or operate lamps.
- Verify lamp identity/readback, then commission.
- Enable automatic control per group and confirm normal operation.

### T22.5 — Repeat for both production modes

- Repeat T22.3–T22.4 for seasonal and schedule production.
- Confirm no test entities appear and only the selected engine's settings are offered.

### T22.6 — Update, rollback and documentation

- Rehearse a normal update to a newer pinned release.
- Rehearse rollback to the previous known-good SHA.
- Finish README/onboarding, troubleshooting, profile-change guidance and release notes.
- Promote the tested adoption release using the same immutable-version discipline as T16.

## Acceptance criteria

- A new controller is provisioned, adopted, commissioned and operational following only
  the published instructions.
- The uncommissioned state cannot issue operational lamp commands.
- A second fresh installation can reuse the same instructions without copying controller
  logic.
- Release is promoted only after CI and hardware checks pass.

## Exit condition

T22 is complete when Gate C is satisfied from a clean starting point and the manual
package installation route remains usable alongside adoption.
