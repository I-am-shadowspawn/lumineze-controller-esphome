# Seasonal production and development profiles

Static-topology seasonal builds use `packages/seasonal-production.yaml` or
`packages/seasonal-development.yaml`. Both include the same
`topology/controller-core.yaml`: one seasonal engine, one policy/dispatch path,
and one evaluation orchestrator. Production selects only
`topology/input-real.yaml`; development selects only
`topology/input-development.yaml`. Existing `lumineze-topology*.yaml` package
names remain compatible aliases. The fixed two-fixture legacy composition
continues at `packages/lumineze-controller.yaml`, with development at
`packages/lumineze-controller-development.yaml`.

Production uses INFO logging, live clock snapshots, operational diagnostics,
and no simulation controls or preview sensors. Development uses DEBUG logging,
adds simulation controls and detailed seasonal diagnostics, and defaults both
simulation input and simulated automatic output to off. The generic development
device file includes `topology/fixture-luminize-development.yaml` alongside
each enabled fixture package to expose its Automatic Preview. The simulation
switches and date/time controls are non-restoring; the simulation cannot
survive restart as an active input or physical output authorization. A fixture
manual level remains an operational control in both profiles.

Both entry points retain the same normal operating settings and calibration
rules. Seasonal context parameters and minimum-change thresholds retain their
existing restoring behavior. Per-fixture calibration remains bound to fixture
identity, slot, product and MAC; the development profile does not add a second
copy. The only profile-specific persisted controls are none: simulation state
and bench authorization reset off, and simulated calendar/time never restore.
The expected operational and development diagnostic entities and sampling
intervals are listed in [diagnostic profiles](diagnostic-profiles.md).

CI config-validates and compiles both generic profiles plus both legacy
profiles. It checks provider isolation in generated production code, compares
live snapshots from the production and development providers, and replays the
seasonal topology engine against 1,600 legacy target cases. This is software
evidence only. Gate A still requires a focused seasonal bench smoke test,
settings capture/restore observations, and confirmation that the live outputs
and Home Assistant controls behave as intended before schedule work is treated
as production-ready.
