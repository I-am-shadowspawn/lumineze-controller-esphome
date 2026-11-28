# T18 — Design bootstrap, adoption and commissioning as distinct states

## Entry conditions and dependencies

- T17 (deployment proof / Gate B) is the declared prerequisite in `todo.md`.
- Current state: T10–T14 software deliveries exist; T15–T17 physical gates are open.
- T18 is **design-only**; it produces the specification that T19 and T20 implement.
- Existing project already has:
  - Four production/development seasonal/schedule profiles in `packages/seasonal-*.yaml` etc.
  - A shared project metadata fragment in `packages/core/project.yaml`.
  - `example/` wrappers that pin an immutable package/component SHA.
  - A custom `lumineze_topology` external component in `components/lumineze_topology/`.
  - A CI matrix in `ci/profile-matrix.json` that validates six configurations on ESPHome 2026.11.0.
  - No `dashboard_import`, no `adopt/` entry point, and no `firmware/` bootstrap.

## Decisions this plan must settle

1. **Bootstrap composition choice**
   - Option A: minimal bootstrap firmware with **no lamp BLE transport at all**.
   - Option B: full controller firmware whose **uncommissioned state blocks** all operational lamp commands.
   - **Recommended:** Option A. It is smaller, faster to install over USB, and cannot accidentally drive a lamp before real MACs are supplied. It still needs Wi-Fi, API/OTA, and a commissioning interlock that the adopted production build enforces.

2. **Provisioning mechanisms for first Wi-Fi setup**
   - Use **captive portal** and **Improv Serial** initially.
   - **Defer BLE Improv** until T21/T22 confirm coexistence with the lamp BLE clients.
   - Rationale: the Pi Hut ESP32-C3 has USB; Improv Serial plus captive portal covers first install without requiring a separate app.

3. **How the user chooses the final profile**
   - Profile selection happens in the **generated local device YAML** after adoption.
   - The bootstrap/adoption entry point is **profile-agnostic**; it only supplies identity, Wi-Fi, API/OTA, and a project pin.
   - The user edits the generated YAML to import one of the four published profile packages and supply fixture MACs.

4. **How lamp MAC addresses are supplied**
   - During adoption, the generated YAML contains **placeholder MACs** and explicit fixture slots.
   - Commissioning requires replacing every placeholder with a real MAC and confirming the topology.
   - Placeholder MACs alone are **not** a safety mechanism; a separate `commissioned` switch/interlock enforces that no operational commands execute until valid MACs are present and the user explicitly enables control.

5. **Uncommissioned-state representation and enforcement**
   - A persisted `commissioned` switch defaults to `false` and resets to `false` on first bootstrap.
   - The common control path checks `commissioned` before any fixture request becomes a pending BLE write.
   - When `commissioned` is false:
     - All automatic/manual/group/fixture requests are rejected or forced to safe-off.
     - The BLE dispatcher does not connect to operational fixture addresses.
     - Diagnostic entities still report identity, clock validity, and commissioning status.
   - Commissioning is a deliberate UI action performed only after the user has verified lamp identity and readback.

6. **Network credentials, API/OTA access, and setup AP handling**
   - Bootstrap starts an access point on first boot if no Wi-Fi is configured.
   - Captive portal allows Wi-Fi provisioning.
   - API and OTA passwords/keys are generated or supplied by the user during adoption, not embedded in public packages.
   - No shared production credentials are shipped in the repository.

7. **Project identity and import URL/version**
   - `dashboard_import` points to a stable, versioned public YAML in `adopt/`.
   - The import uses `import_full_config: false` so Device Builder generates a small local wrapper.
   - The adopted wrapper imports the same package and external-component SHA as the chosen profile examples.

## Proposed state machine

```text
[Factory / erase]
    |
    v
[Bootstrap firmware flashed]
    |
    v
[Setup AP / Improv Serial / captive portal]  <-- user supplies Wi-Fi
    |
    v
[Wi-Fi configured, online, unadopted]
    |
    v
[ESPHome Device Builder discovers and adopts]
    |
    v
[Device Builder generates local wrapper]  <-- user may edit before install
    |
    v
[Production/development profile installed]  <-- build-time engine selected
    |
    v
[Uncommissioned controller]  <-- persisted commissioned=false
    |
    +--> user supplies real MACs, validates topology, verifies readback
    |
    v
[Commissioned=true, automatic control still off by default]
    |
    +--> user enables group automatic control per group
    |
    v
[Normal operation]
```

Key rule: **lamp operation becomes possible only after the explicit commissioning step**, not merely after adoption or profile installation.

## Bootstrap firmware design

- **Path:** `firmware/bootstrap.yaml`
- **Responsibilities only:**
  - Board/framework/logger setup
  - Project identity (`packages/core/project.yaml`)
  - Wi-Fi (station + fallback AP + captive portal)
  - Improv Serial support
  - API and OTA support with user-supplied credentials
  - A single commissioning-status diagnostic (always reports `Uncommissioned`)
  - **No BLE lamp client, no topology engine, no control groups, no dispatcher.**
- **Why this is safe:** bootstrap cannot accidentally send lamp commands because the lamp transport is absent.
- **Profile label:** `bootstrap`
- **Transition:** user installs a production/development profile YAML that includes the full controller packages. The profile carries its own `commissioned` default of `false`.

## Adoption entry point / `dashboard_import` design

- **Path:** `adopt/lumineze.yaml`
- Contains a `dashboard_import` block with:
  - `package_import_url`: points to `adopt/lumineze.yaml` at a pinned ref.
  - `import_full_config: false`.
- The imported package defines:
  - Substitutions for `device_name`, `friendly_name`, `area_name`, `timezone`.
  - `wifi` and `api`/`ota` placeholders that Device Builder fills from its own secrets flow.
  - Project metadata inclusion.
  - A comment block telling the user to select a profile package and supply fixture MACs.
- The **generated local YAML** then adds one of the four profile packages, e.g.:

```yaml
packages:
  lumineze.adopt: github://I-am-shadowspawn/lumineze-controller-esphome/adopt/lumineze.yaml@${controller_ref}
  lumineze.profile: github://I-am-shadowspawn/lumineze-controller-esphome/packages/seasonal-production.yaml@${controller_ref}
```

- The profile package brings in the engine, topology, controls, dispatcher, and commissioning interlock.

## Commissioning interlock

- **Path:** `packages/topology/commissioning.yaml` (linked from `controller-core.yaml`).
- **Entity:**
  - `topology_commissioned` — template switch, `RESTORE_DEFAULT_OFF`. This is the single point of safety.
  - `topology_commissioning_status` — text sensor that shows whether all enabled fixtures have non-placeholder MACs and whether the controller is commissioned.
  - `topology_commission` — button to set the commissioned switch on.
  - `topology_decommission` — button to set the switch off.
- **Enforcement points:**
  - `apply_topology_policy` checks `topology_commissioned`. While false, fixtures receive `HOLD` status and any non-SAFETY pending request is revoked. Status text reads "Controller not commissioned; output held".
  - The decommission action calls `topology_safe_off_all` to clear controls and request off, then the next policy pass holds all subsequent requests.
  - The bootstrap firmware has no fixtures, so the real enforcement is the absence of the BLE transport.
- **MAC address validation:**
  - A placeholder MAC is defined as a value that matches `00:00:00:00:00:00`, is an empty secret, or contains the literal string `placeholder`.
  - The `topology_commission` button is a simple interlock reminder; complete MAC validation is performed at **profile configuration** by `lumineze_topology` using `mac` values that are real or explicitly placeholder with `enabled: false`.

## Security and recovery considerations

- No shared production credentials in public packages; all secret values come from the user's private `secrets.yaml` or from Device Builder.
- Bootstrap OTA/API keys must be user-configurable before adoption.
- A factory reset returns to bootstrap and clears persisted commissioning state.
- Recovery path: reflash bootstrap, re-adopt, or install a known-good local YAML pinned to a previous SHA.
- The uncommissioned profile build still validates and compiles with placeholder MACs, but it cannot operate lamps.

## Incremental deliverables

| ID | Deliverable | Acceptance | Physical? |
| --- | --- | --- | --- |
| T18.1 | Decision record and state diagram | Design reviewed and approved by owner; matches constraints above | No |
| T18.2 | Bootstrap composition specification | `firmware/bootstrap.yaml` draft with no lamp transport; CI fixture defined; size estimate provided | No |
| Tesp the Bootstrap package includes project metadata and a fallback AP; profile-agnostic | No |
| T18.4 | Commissioning interlock specification | `packages/topology/commissioning.yaml` with switch, buttons and status; fixture-policy integration point identified; no new physical claims | No |
| T18.5 | Integration handoff to T19/T20 | T19 and T20 plans exist and carry T18 decisions; open T18 questions resolved | No |

## Acceptance criteria for T18 as a profile design change

- The design specifies every transition in the state machine.
- The exact point at which lamp operation becomes possible is documented and enforced by design, not just by UI convention.
- Dynamic BLE discovery/pairing is explicitly out of scope.
- Bootstrap is minimal and contains no operational lamp transport.
- Adoption entry point is compileable without installation-specific secrets.
- Placeholder MACs are coupled with an explicit commissioning interlock.
- Profile selection remains build-time; no runtime mode switching is implied.
- Provisioning methods are limited to captive portal and Improv Serial initially; BLE Improv is deferred.
- Network/API/OTA credentials are user-supplied, not shared in public files.

## Exit / handoff to T19 and T20

- T19: implement and test the bootstrap firmware on real boards (two boards, unique provisioning, no operational lamp output).
- T20: implement and test the `dashboard_import`, generated wrapper, and commissioning transitions.
- T21: extend CI to validate `firmware/bootstrap.yaml`, `adopt/lumineze.yaml` (no secrets) and a commissioned fixture, while preventing profile and project identity regressions.
- T22: end-to-end fresh-install rehearsal through Device Builder.

## Implementation status

This document is **design and the software scaffold** for T18. The actual Wi-Fi provisioning, Device Builder, and board testing remain the physical gates for T19/T20.
