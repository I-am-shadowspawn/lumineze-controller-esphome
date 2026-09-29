# T02 — Build and private configuration boundary

Repository: public `I-am-shadowspawn/lumineze-controller-esphome`, default branch `master`. No licence file is present, so the repository currently grants no explicit reuse licence; add one only after the owner chooses it. This task retains the existing repository name and visibility.

## Supported checkpoint

- Python 3.12 and `esphome==2026.9.0` (single pin in `requirements-ci.txt`).
- The checked-in `esp32` configuration selects ESP-IDF on an ESP32-C3. The validated ESPHome version resolved ESP-IDF **5.5.5** and RISC-V GCC **14.2.0** locally. The deployed controller's toolchain remains unknown; this is a reproducible repository checkpoint, not a claim of upgrade compatibility.
- The `ci/controller.yaml` fixture includes `../packages/lumineze-controller.yaml` from the current checkout. Its name, MACs, Wi-Fi and API key are public dummy values. Never flash it to an animal enclosure.
- CI validates four enable-flag combinations and compiles the two-light fixture from the checked-out source.

## Clean-checkout build

From the repository root on a Linux machine with Python 3.12, Git, a C/C++ build environment and network access for the ESP-IDF toolchain:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-ci.txt
.venv/bin/esphome config ci/controller.yaml > /dev/null
.venv/bin/esphome compile ci/controller.yaml
```

ESPHome writes generated files under `ci/.esphome/`; this and `.venv/` are ignored. The local test on 29 September 2026 built the JungleDawn-only fixture successfully: image 1,397,414 bytes, 76.2% of the 1,835,008-byte application partition; static RAM estimate 148,348 of 321,296 bytes (46.2%). These are **build estimates**, not measured runtime heap or a flashed-hardware result. A local cache permission issue was resolved by setting `CCACHE_DIR` to a writable temporary directory; ordinary GitHub runners should supply one.

## Private inputs and fixtures

Real controllers keep their small YAML and `secrets.yaml` outside this public repository or under ignored `devices/`/`private/`. The local YAML owns device identity and area, timezone, explicit lamp enable flags and real MACs, Wi-Fi, API encryption, and any fallback AP/OTA credential. Do not commit expanded configurations, build logs, firmware binaries, settings exports or real MAC addresses. The public `example/` YAML is a template; `ci/` files are dummy build inputs, with names prefixed `lumineze-ci`.

The fallback AP and `captive_portal` are now supplied by local YAML, as shown in `example/vivarium-example.yaml`. Existing local YAMLs that set only `fallback_ap_ssid`/`fallback_ap_password` substitutions must move those values under `wifi.ap` and add `captive_portal:` before updating; otherwise both facilities will be absent. This is a configuration migration, and must be checked before changing a live controller.

## T04 package checkpoint

The package exposes `device_name`, `friendly_name`, `area_name`, `timezone`, `enable_jungle_dawn`, `enable_prot5`, `jungle_dawn_mac` and `prot5_mac`. A real MAC is required for each enabled lamp; a disabled lamp may use the internal zero-MAC placeholder. Local YAML supplies Wi-Fi/API credentials and, when wanted, the fallback AP. The shared package has no `!secret` lookup or credential default. Both SNTP and Home Assistant time entries now use the same timezone substitution.

On 29 September 2026, the resolved `ci/controller.yaml` configuration before and after moving the fallback AP was identical after excluding the two now-unused fallback substitutions; key order changed only because the local include is merged last. The fixture then gained an explicitly dummy API key to exercise the local encryption overlay. `esphome config` passed for the one-light local YAML without an AP. A full two-light `esphome compile` passed with ESPHome 2026.9.0 / ESP-IDF 5.5.5: image 1,438,754 bytes (78.4% of the application partition), static RAM estimate 148,380 bytes (46.2%). The fixture changed to add API encryption, so its size is not directly comparable to the earlier build. Hardware equivalence remains unverified pending T01 field observations.

The full-build workflow also passed on GitHub for both the [branch push](https://github.com/I-am-shadowspawn/lumineze-controller-esphome/actions/runs/36552309136) and [pull request](https://github.com/I-am-shadowspawn/lumineze-controller-esphome/actions/runs/36552339956). Both runs checked out the proposed commit, validated all four lamp combinations and compiled the two-light fixture.

The archive contains no literal Wi-Fi password, API key or lamp MAC, but it does retain the old device identity, area and fallback AP SSID. Its `!secret` references need private values before it can build. `docs/baseline.md` records the sanitised source comparison and the unresolved hardware/recovery evidence. Do not treat the archive as an exact private backup or as verified deployed firmware.

To recover a live device, use a privately saved known-good YAML/secrets/settings set and its verified Git ref, rebuild with the ESPHome version used for that build, then use the previously tested USB/serial or OTA path. The exact deployed ref, compiler version and working physical recovery route still need owner confirmation before migration.
