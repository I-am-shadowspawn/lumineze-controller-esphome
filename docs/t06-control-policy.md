# T06 — Common control policy and transport boundary

Historical implementation checkpoint. The planned T06R evolution to contexts,
groups and independently identified fixtures is in the
[architecture](plans/fixture-topology-architecture.md) and
[runbook](plans/fixture-topology-implementation.md). That plan is not implemented
by this document and does not replace the recorded validation evidence below.

The seasonal engine now publishes a mode-independent pair of desired fractions
and peak fractions, plus validity and simulated-input flags. It does not read
dispatcher state or submit BLE commands. `core/control.yaml` turns each
authorised fraction into a final percent, applies the lamp's maximum once, and
submits the result to `queue_lumenize_command`. Manual buttons and safe-off
also use `submit_control_target`. Only that script calls the queue in the
supported package.

## Policy

| Situation | Outcome |
| --- | --- |
| Boot before valid SNTP time | Automatic controls default off; restored automatic-on waits for valid time. No boot hook sends a level. |
| Clock remains valid after a missed sync | The baseline has no time-since-sync cutoff. Control continues from the ESPHome clock until it reports invalid; the last sync source remains visible. A freshness cutoff would be a separate policy change. |
| Invalid clock before grace | Existing output and pending request are held. A manual request is allowed. |
| Invalid clock after grace with fail-safe enabled | A 0% safety request takes precedence over manual and automatic requests for each enabled lamp. It is retried by normal BLE policy. A manual nonzero request is rejected until time is valid or fail-safe is disabled. |
| Fail-safe disabled | Invalid time holds output; it does not infer or confirm that the lamp is off. |
| Invalid or non-finite engine output or maximum | Automatic output is held and its pending retry is cancelled. The per-lamp invalid-output diagnostic becomes active. |
| Automatic switched off | Pending automatic request is cancelled; physical state is held. No off command is implied. |
| Manual override switched on | Pending automatic request is cancelled. The requested manual level is capped by the configured maximum; override lasts until switched off and is not restored after reboot. |
| Explicit safe-off | Automatic and manual modes are switched off, then 0% is queued for each enabled lamp. This is a request, not proof of physical output. |
| Simulated solar input | Automatic BLE output is paused; manual controls remain available. As in the baseline, simulated input also bypasses invalid-clock fail-safe; T07 must isolate this development facility from production. |
| Unavailable lamp | Its retries and eventual communication fault remain per lamp; the other lamp can dispatch after the shared quiet time. No request to an unavailable lamp is treated as a confirmed state. |

Automatic fractions are multiplied by the configured maximum and rounded once
with `std::lround`; manual integer percentages are capped at the rounded
maximum. ProT5's default maximum of 0 therefore produces 0%. Minimum-change,
endpoint and periodic recovery decisions use final percentages in the common
policy. A per-lamp diagnostic shows when the configured maximum reduced a
requested output. The dispatcher has no solar, manual or brightness-limit
knowledge.

The latest authorised target replaces an older pending target. A transaction
copies its target and request generation when it starts. A newer request stays
pending after the older write completes or fails. Cancelling a request advances
the generation, so an in-flight completion or failure cannot recreate a
cancelled pending command. An in-flight BLE write cannot be recalled; a newer
safety request waits for the transaction sequence and then uses the normal
quiet-time and retry limits.

The last reported lamp value is retained separately from requested, pending,
in-flight and completed values. Readback freshness is cleared when a new
transaction starts. If an off request fails or has no fresh readback, the
physical level remains unknown and the diagnostic state says so.

## Recorded changes from the baseline

- An in-flight automatic request cancelled by manual mode, test mode or
  automatic-disable can finish, but will no longer retry or reappear as pending
  afterward.
- Once invalid-time safe-off is active, manual requests cannot supersede it.
  Before the grace period, manual control remains available.
- Control status and invalid-output diagnostic entities are added. The existing
  seasonal curve status entities now report the calculated preview; the new
  control status entities report whether a target was queued, held or rejected.
- The existing lamp calibration, retry intervals, restore defaults, public
  package entry point and BLE wire protocol are retained.

## Verification

- ESPHome 2026.9.0 validates all four enable-flag combinations.
- The two-light ESP32-C3/ESP-IDF firmware compiles. The image is 1,442,004
  bytes (78.6% of the application partition); static RAM estimate is 149,044
  bytes (46.4%). These are build estimates, not runtime measurements.
- `python3 scripts/check_transport_scenarios.py` compiles and executes the
  actual dispatcher and completion lambda bodies with a simulated transport.
  It covers newer target replacement, cancellation during a transaction,
  failure with a newer target, and progress for the other lamp while one is
  unavailable. CI runs the same check.

The simulator does not emulate BLE radio behaviour or a physical lamp. A
hardware observation remains necessary before updating the deployed
vivarium from its known-good `v1.0.0` recovery source.
