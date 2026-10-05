# T14 — Minimal examples and installation documentation

**Entry/dependencies:** T13 public identity/compatibility decisions. Draft user
journeys now; validate actual candidate profiles after T11–T13.
**Delivery:** a remote consumer can build and commission without copying logic.

## User and composition contract

Use the established Pi Hut ESP32-C3, ESP-IDF and manual Device Builder route.
Document prerequisites in end-user order: Home Assistant/ESPHome basics, YAML,
private Wi-Fi/API/OTA values, correct lamp MAC mapping, calibration and requested
versus reported output. Default recommendation is seasonal production after
verification; schedule is an explicit profile choice, development is for bench
work. Bootstrap/adoption belongs to T18–T22.

Reuse the existing `example/` directory and `secrets-example.yaml` naming rather
than creating a second example tree. Maintain explicit contexts, role groups,
fixture identities/slots and repeated fragments. Pin package and external
component to one immutable candidate/release revision. Runtime controls never
change MACs, routing or engine selection.

## Incremental deliveries

- [ ] **T14.1 — Public wrapper contract.** Inventory required/optional variables
  and fragments for each profile, plus legacy adapter compatibility. Document
  timezone, IDs, enabled/disabled descriptors, connection allocation and
  experimental topology. Acceptance: every field is explained; no missing-MAC
  convention, slot/product assumption or unsupported topology is recommended.
- [ ] **T14.2 — Four minimal examples and private boundary.** Provide four
  wrappers or one unambiguous template with fully validated alternatives. Use
  obvious explanatory placeholders and a valid dummy-secret CI copy; document
  generation of unique encryption/access credentials. Acceptance: examples
  contain only installation data/profile selection, never duplicated engine,
  policy or dispatcher code; secret values are excluded from commits/artifacts.
- [ ] **T14.3 — End-user installation and commissioning.** Document validate,
  compile, USB installation, HA integration, fixture identification, initial
  automatic-off state, ProT5 zero default, calibration, manual low/off readback
  checks, then deliberate automatic enable. Include schedule Apply/edit rejection
  and seasonal T23 workflows with capability/support status. Acceptance: physical
  confirmation is distinct from a successful upload or requested off value.
- [ ] **T14.4 — Upgrade, profile switch and recovery guides.** Provide a field
  mapping for v1→generic and seasonal↔schedule, capture/export of settings,
  incompatible preference handling, HA automation updates and pinned rollback.
  Document development→production removal of test state. Acceptance: no claim of
  automatic settings migration or preservation without T15 evidence.
- [ ] **T14.5 — Clean remote consumer rehearsal.** Build from an empty consumer
  directory outside the checkout with candidate SHA references and dummy secrets.
  Validate/compile all supported alternatives without local helper assets or
  generation scripts. Record exact files/commands and resolved references.
  Acceptance: nested includes/component assets resolve at the same revision;
  another person can follow the instructions, with installation friction tracked
  for T17. Refresh final examples to the verified stable tag in T16.

## Completion and rollback

Keep build proof separate from physical commissioning proof. Roll back broken
example/profile changes without replacing working installation data. Existing
manual package routes stay documented alongside future adoption work.

## Execution and evidence rules

Use the [delivery index](t10-t17-delivery-index.md) for gate definitions and the
baseline. The checkboxes below are the canonical incremental tracker for this
task. Complete each increment in a separate reviewable commit after its checks
pass. Record source SHA, files, commands/results, evidence links, deviations and
remaining work beside that increment. Proposed filenames may change; ownership
and acceptance criteria may not silently change. Do not mark implementation or
hardware increments complete because this plan exists.

**Progress:** all increments planned; no implementation or hardware evidence
is claimed by this document.
