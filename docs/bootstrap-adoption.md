# Bootstrap and adoption (T18–T22)

This page describes the bootstrap/adoption work introduced by T18. T19/T20
define and track the Device Builder and hardware gates; T21 extended CI to the
adoption artifacts; T22 defines the fresh-install rehearsal. Software proof is
collected in `docs/evidence/t19-t22-software.md`.

## Files introduced

| File | Purpose |
| --- | --- |
| `firmware/bootstrap.yaml` | Minimal, lamp-transport-free image for first USB install. |
| `adopt/lumineze.yaml` | `dashboard_import` entry point for ESPHome Device Builder. |
| `packages/topology/commissioning.yaml` | Commissioning switch, buttons and status sensor. |
| `example/bootstrap.yaml` | Public wrapper for the first USB install. |
| `example/adopted-seasonal-production.yaml` | Adopted wrapper: adoption entry point plus seasonal production profile. |
| `example/adopted-schedule-production.yaml` | Adopted wrapper: adoption entry point plus schedule production profile. |
| `ci/bootstrap.yaml`, `ci/adopted-seasonal.yaml`, `ci/adopted-schedule.yaml` | CI fixtures for bootstrap and adopted composition. |
| `scripts/check_bootstrap_isolation.py` | Resolved-config proof: no lamp transport, correct identity, dummy CI boundary. |
| `scripts/check_adopted_examples.py` | Adopted example contract plus offline end-to-end resolution. |
| `docs/plans/t18-bootstrap-adoption-design.md` | Design decisions and state machine. |
| `docs/plans/t19-bootstrap-implementation.md`…`t22-fresh-install.md` | Implementation and rehearsal plans. |
| `docs/evidence/t19-t22-software.md` | Software evidence, measured footprints, open hardware work. |

## State machine

```text
Factory / erase
    ↓
Bootstrap firmware flashed over USB
    ↓
Wi-Fi provisioned (Improv Serial or captive portal)
    ↓
Discovered and adopted in ESPHome Device Builder
    ↓
Local YAML generated; user selects profile and supplies MACs
    ↓
Production/development profile installed
    ↓
Uncommissioned controller (no operational lamp output)
    ↓
User commissions after verifying identity/readback
    ↓
User enables automatic control per group
    ↓
Normal operation
```

## Commissioning interlock

The `topology_commissioned` switch defaults to off and restores off. While it is
off:

- `apply_topology_policy` forces every fixture to `HOLD` and revokes any pending
  request.
- The dispatcher receives no new operational targets.
- Diagnostic entities still report identity, clock validity and commissioning
  status.

Pressing **Decommission Controller** turns the switch off, forces safe-off, and
leaves the controller in the non-operational state.

## Next steps

- T19: remaining work is hardware-only (setup AP, Improv/captive portal
  provisioning, credential persistence, two-board independence); the compile,
  identity and isolation work is done and evidenced.
- T20: remaining work is Device-Builder-only (generated YAML inspection,
  commissioning/decommissioning transitions); adopted composition is covered
  by `ci/adopted-*.yaml` and the public adopted examples.
- T21: done in-repo — CI validates and compiles the bootstrap and adopted
  fixtures, runs the isolation/adopted-example checks and the public example
  verification; the four advertised profiles remain the only `profiles`
  entries.
- T22: plan written (`docs/plans/t22-fresh-install.md`); the rehearsal itself
  needs a board and a pushed T18-containing SHA to pin.
