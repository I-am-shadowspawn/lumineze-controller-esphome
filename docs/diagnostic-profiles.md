# Diagnostic profiles

Production profiles expose operational health so Home Assistant can show
whether a controller is working and what each lamp last did. Development
profiles add calculation internals and preview values for commissioning and
troubleshooting. The development profiles use DEBUG logging; production uses
INFO, which retains transaction and fault messages without a per-notification
lamp report trace.

## Legacy two-lamp package

`packages/lumineze-controller.yaml` is the fixed legacy production composition.
For static topology builds, `packages/seasonal-production.yaml` is the
production entry point and `packages/seasonal-development.yaml` is the
development entry point. The `lumineze-topology*.yaml` paths remain aliases.
The legacy development counterpart,
`packages/lumineze-controller-development.yaml`, adds
`packages/features/verbose-diagnostics.yaml` and enables DEBUG logging.

Both profiles expose connection, command-pending, readback-freshness and
readback-mismatch state for JungleDawn and ProT5; controller time validity;
time fail-safe and active-transaction state; per-lamp communication faults,
control-output validity and brightness-limit state; requested/pending target,
last completed level, last reported level, completed and failed transaction
counters; dispatcher, control and readback status; last completion/report time;
and seasonal-engine status. The seasonal package owns the solar-validity,
UV-window, curve, sunrise/noon/sunset and evaluation-status entities, so those
entities are only declared when that engine is included.

Development adds these detailed seasonal calculation entities:

- Solar Calendar Day, Solar Effective Day, Solar Declination, Solar Day Length,
  Simulated Solar Elevation and Solar Daylight Envelope.
- JungleDawn Curve Fraction, Seasonal Position, Effective Peak, Calculated
  Target and Last Automatic Queued Target.
- ProT5 UVB Window Length, Window Envelope, Curve Fraction, Effective Peak,
  Calculated Target and Last Automatic Queued Target.
- Simulated Sun Above Horizon.

The operational target/report/counter sensors update every 1–5 seconds. The
development calculation sensors update every 10 seconds. Detailed seasonal
`ESP_LOGD` traces are visible in development at DEBUG and suppressed in
production at INFO.

At those intervals, the legacy operational profile schedules about 216
diagnostic sensor evaluations per minute. Development adds about 102 numeric
evaluations per minute plus one binary-sensor evaluation per minute. In the
generic profile, each fixture schedules five operational sensor evaluations
every 5 seconds (60 per minute); development adds one preview evaluation every
10 seconds (6 per minute) per fixture. The context and group sensors add 18
evaluations per minute per context/group pair. These are configured sampling
ceilings, not BLE activity or Home Assistant network-message counts: ESPHome
only publishes state changes unless `force_update` is enabled. The development
addition therefore has no effect on lamp traffic, and its HA traffic depends
on how often calculated values change.

## Generic topology package

Both generic profiles include controller time validity, context evaluation
status and visible/UV demand, plus each group's delivery state. Each fixture
exposes BLE connection, request-pending, readback-fresh and readback-mismatch
binary sensors; requested, completed and lamp-reported levels; completed and
failed transaction counters; and dispatch/readback status text sensors. The
five numeric per-fixture operational sensors update every 5 seconds.

The production composition uses `packages/topology/fixture-luminize.yaml`.
Development adds `packages/topology/fixture-luminize-development.yaml` once
per fixture. This adds that fixture's Automatic Preview sensor, updated every
10 seconds. The generic development controller also includes the simulation
controls supplied by its development input provider. They are not present in
the production input provider.

## CI inventory checks

The workflow compiles the legacy and generic production/development examples.
`scripts/check_diagnostic_profiles.py` then checks generated source for
representative shared operational entities and asserts that the legacy solar
calculation details and generic automatic preview appear only in development.
The source check intentionally samples the profile boundary; the inventories
above document the full intended entity groups.
