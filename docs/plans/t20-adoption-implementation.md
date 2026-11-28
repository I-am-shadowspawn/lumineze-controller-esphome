# T20 — Implement dashboard adoption and explicit lamp commissioning

**Depends on:** T19 bootstrap proven.  
**Intent:** make Device Builder generate a small, maintainable local wrapper and
enforce that an uncommissioned adopted controller cannot operate lamps.

**Status (in repo):** the software side of T20.2 is complete —
`adopt/lumineze.yaml`, the adopted seasonal/schedule CI fixtures and the two
adopted public examples validate and compile, and the commissioning interlock
is enforced by `packages/topology/fixture-policy.yaml`;
`scripts/check_adopted_examples.py` verifies the example contract offline.
T20.1/T20.3–T20.5 require Device Builder and a board.

## Decisions already settled by T18

- `adopt/lumineze.yaml` provides the `dashboard_import` entry point with
  `import_full_config: false`.
- The generated local YAML selects one of the four profiles and supplies fixture MACs.
- Commissioning is controlled by a persisted `topology_commissioned` switch that
  defaults off.
- Placeholder MACs are coupled with the commissioning interlock, not treated as
  a safety mechanism on their own.

## Remaining work

### T20.1 — `dashboard_import` validation

- Confirm the import URL resolves and Device Builder offers the package.
- Inspect the YAML that Device Builder generates.
- Verify it does not contain `import_full_config: true`.

### T20.2 — Generated wrapper compile test

- Take the generated YAML, add a profile selection, fixture MACs and secrets.
- Validate and compile the adopted profile locally and in CI.
- Confirm the build includes the commissioning interlock and identity sensors.

### T20.3 — Commissioning state transitions

- Flash the adopted-but-uncommissioned profile.
- Confirm `topology_commissioned` is off after first boot and after reboot.
- Confirm no BLE connection attempts are made to the supplied MACs.
- Confirm `topology_commissioning_status` reports the uncommissioned state.

### T20.4 — Decommission behavior

- Commission the controller, enable a group automatic control, and verify output.
- Press `Decommission Controller`.
- Confirm controls are forced off, all operational output is held, and BLE
  activity stops.

### T20.5 — Incomplete/invalid commissioning

- Flash a wrapper with placeholder MACs.
- Confirm the profile validates and compiles (placeholders are syntactically valid).
- Confirm the controller remains safe because `topology_commissioned` is off,
  regardless of MAC validity.
- Document that real MACs must be supplied before commissioning.

### T20.6 — Handoff to T21/T22

- Record adoption evidence, including generated YAML, commissioning transitions,
  and any Device Builder friction.
- Update examples and installation docs based on observed generated output.

## Acceptance criteria

- Device Builder adoption produces a compilable wrapper.
- The adopted controller starts in an uncommissioned, non-operational state.
- Commissioning is explicit; decommissioning forces safe-off and stops output.
- No hidden edits to upstream packages are required.

## Exit condition

T20 is complete when the adoption flow is demonstrated on real hardware and
the CI matrix covers the adopted configuration.
