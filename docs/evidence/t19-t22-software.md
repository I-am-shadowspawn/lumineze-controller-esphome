# T19–T22 software evidence

Scope: the software portions of T19–T22 that can be proven without a board.
Hardware-dependent sections of T19.2–T19.5, T20.1/T20.3–T20.5 and T22.1–T22.5
remain open and are listed under "Still hardware-dependent".

Toolchain: local `.venv` with `esphome==2026.11.0`, resolving ESP-IDF **5.5.6**
on ESP32-C3 (matches `ci/profile-matrix.json` `toolchain`).

## T19.1 — Bootstrap compile, identity and isolation

Fixture: `ci/bootstrap.yaml` (includes `firmware/bootstrap.yaml`).

- `esphome config ci/bootstrap.yaml` — valid.
- `esphome compile ci/bootstrap.yaml` — full compile passed.
- `python scripts/check_bootstrap_isolation.py` — resolved configuration
  asserts: no `ble_client`, no `lumineze_topology` section, no
  `external_components`, project `shadowspawn.lumineze`, build profile
  `bootstrap`, captive portal and Improv Serial present,
  `topology_commissioned` `RESTORE_DEFAULT_OFF` with `lambda: return false;`,
  and dummy CI credentials only (Wi-Fi `ci-network`/`ci-password`, setup AP
  password forced off the published `lumineze-setup` default).

## T20.2 — Adopted wrappers compile (composition without a Device Builder)

Local adoption fixtures (Device-Builder-shaped wrapper: adoption entry point
plus one production profile):

- `ci/adopted-seasonal.yaml` — `esphome config` and full compile passed.
- `ci/adopted-schedule.yaml` — `esphome config` and full compile passed
  (visible `jungle_dawn` + UV `prot5`, two roles).
- `python scripts/check_ci_artifacts.py adopted-* --skip-artifacts` — dummy
  Wi-Fi credentials, no `wifi: ap:`, no API key, dummy lamp addresses.

Public adopted examples resolved as ordinary Git-package consumers from an
empty temporary directory:

- `python scripts/check_adopted_examples.py` — static contract (one immutable
  `controller_ref`, three `ref: ${controller_ref}` pins, adoption entry point,
  profile package, `import_full_config: true` rejected, secrets-only
  credentials) plus end-to-end resolution against the **working tree** through
  a temporary `git commit-tree` commit, with no network access. Both
  `example/adopted-seasonal-production.yaml` and
  `example/adopted-schedule-production.yaml` validated.
- All six public wrappers (four classic adopted-free examples, two adopted
  examples) and the bootstrap example must share one pinned SHA; the checker
  rejects drift.
- `--remote` mode fetches the pinned GitHub SHAs and is reserved for the
  post-push release rehearsal once a SHA containing `adopt/lumineze.yaml`
  exists upstream.

## T21 — CI and release-check extension

- `ci/profile-matrix.json` gains `adoption_artifacts` outside `profiles`; the
  four advertised runtime profiles remain the only `profiles` entries
  (`check_profile_manifest.py` asserts both).
- `scripts/check_bootstrap_isolation.py`, `scripts/check_adopted_examples.py`
  and the adopted input boundary run in the `validate` job; the three
  adoption fixtures `esphome compile` in the compile step.
- `check_public_examples.py` now runs in the `remote-consumer` job ahead of
  the remote consumer rehearsal (it was previously released-only).
- Release metadata (`check_release_metadata.py`) is unchanged by the new keys
  and still requires the four generic profiles in `release/candidate.json`.

## Measured footprints (ESP32-C3, ESP-IDF 5.5.6, `esphome compile`)

Re-measured after rebasing onto `origin/development` (which added
development-only restart diagnostics; production builds changed by −8 flash
bytes).

| Artifact | Static RAM (bytes) | Flash (bytes) | Notes |
| --- | ---: | ---: | --- |
| `ci/bootstrap.yaml` | 102,108 | 856,296 | smallest; no BLE transport |
| `ci/adopted-seasonal.yaml` | 142,588 | 1,242,616 | adoption + seasonal production |
| `ci/adopted-schedule.yaml` | 148,180 | 1,258,710 | adoption + schedule production |
| `ci/topology-generic.yaml` (seasonal-production fixture) | 145,180 | 1,253,054 | reference profile |

All inside the static budgets (180,000 RAM / 1,600,000 flash); bootstrap uses
about 57% of profile-class flash, confirming "bootstrap is smaller than the
full profiles" without relying on the budget alone.

## Validation commands

```bash
.venv/bin/esphome config ci/bootstrap.yaml
.venv/bin/esphome config ci/adopted-seasonal.yaml
.venv/bin/esphome config ci/adopted-schedule.yaml
.venv/bin/esphome compile ci/bootstrap.yaml
.venv/bin/esphome compile ci/adopted-seasonal.yaml
.venv/bin/esphome compile ci/adopted-schedule.yaml
.venv/bin/python scripts/check_bootstrap_isolation.py .venv/bin/esphome
.venv/bin/python scripts/check_ci_artifacts.py adopted-seasonal --skip-artifacts --esphome .venv/bin/esphome
.venv/bin/python scripts/check_ci_artifacts.py adopted-schedule --skip-artifacts --esphome .venv/bin/esphome
.venv/bin/python scripts/check_adopted_examples.py --esphome .venv/bin/esphome
```

## Still hardware-dependent

- T19.2–T19.5: first-boot setup AP, Improv/captive-portal provisioning,
  credential persistence across reboot, two-board independence.
- T20.1: actual Device Builder adoption (generated YAML inspection).
- T20.3–T20.5: commissioning/decommissioning transitions, placeholder-MAC
  safety on a live board.
- T22.1–T22.5: full fresh-install rehearsal on a blank board, update and
  rollback rehearsal; T22.6 documentation is complete in-repo and the release
  promotion itself awaits a T18-containing SHA for the pinned refs
  (`adopt/lumineze.yaml`, adopted examples, bootstrap example).
