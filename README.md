# LuminEZE ESPHome controller

ESPHome packages for JungleDawn and ProT5 vivarium lighting.

The original two-product configuration remains available at
`packages/lumineze-controller.yaml` for controllers pinned to a v1 release.
The new static-topology controller starts at `packages/lumineze-topology.yaml`.
It supports explicit fixture IDs, slots, product roles, control groups and one
or two seasonal contexts. See [the generic controller guide](docs/topology-controller.md)
and [the Device Builder example](example/topology-two-lamps.yaml) before
preparing a new installation or migration.

Three- and four-fixture configurations require an explicit experimental opt-in.
They compile in CI, but physical ESP32-C3/BLE reliability has not yet been
established. Keep an existing live controller pinned to its known-good tag
until its replacement topology is calibrated and tested on hardware.
