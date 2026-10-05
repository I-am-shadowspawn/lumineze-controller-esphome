# T23 ESP32-C3 bench validation

**Status: planned; no physical trace has been captured.** Software tests do not
complete this gate. Use the tested Pi Hut ESP32-C3 Bluetooth proxy board and an
isolated commissioned LuminEZE lamp. Record Gate A evidence alongside this run.

## Preparation and evidence

1. Record firmware commit SHA, ESPHome version (CI pin), profile, board,
   fixture/group/context topology, lamp product/firmware and timezone. Redact
   secrets and MAC addresses. Save the YAML substitutions and calibration,
   permanent maximum, seasonal settings, minimum-change and retry intervals.
2. Start with the generic seasonal production profile, valid live local time,
   automatic group enabled, manual controls off and both temporary modes off.
   Save initial requested, completed and reported levels and freshness.
3. Capture timestamped serial/API logs plus Home Assistant entity histories.
   For each action/evaluation/transaction, record normal calculated target,
   temporary mode/status, active indicators, time remaining, requested level,
   completed level, reported level, readback freshness/mismatch, pending state,
   completed/failure counts and dispatch/readback status. The development
   profile exposes additional calculated inputs; repeat there with simulation
   disabled. Use those inputs and the saved calibration to derive the normal
   final integer target. If tracing generations/tokens requires extra logging,
   use a separate bench build and retain its diff and SHA.
4. Sample often enough to retain each transaction (serial capture plus entity
   histories; the five-second entity refresh alone may miss intermediate
   events). Label action time, write completion, response and disconnection.
   Keep raw logs, annotated CSV and a short pass/fail report under a dated
   evidence directory. Do not publish credentials.

## Daily maximum: full live rise/hold/descent

Use a day/seasonal configuration whose normal peak exceeds 60%. Keep the
permanent calibrated limit suitable for the lamp. Daily maximum requires live
time; simulated dates are rejected and cannot substitute for this sequence.
Allow a full real rise and descent, or adjust supported seasonal settings on
this isolated bench while preserving the live clock; record every adjustment.

- Apply 60% below the cap. Observe armed state and ordinary at/below-cap
  commands. Editing the staged number alone must have no operational effect.
- Capture normal targets above 60%, while requested output stays at the last
  authorized level <=60%. The normal peak and seasonal settings stay unchanged.
- Capture the first normal target <=60% after exceedance. Mode clears and the
  descending target is submitted even if minimum-change would suppress it.
  Test equality and a skipped-equality descent in separate runs. No duplicate
  is needed when the same target is already confirmed.
- Apply/lower the cap while requested/completed/reported output is 80%.
  Confirm a corrective <=60% request; record the interval until fresh matching
  readback. Apply during an in-flight high write too: it may physically finish,
  but cannot restore its request or confirm the new generation.
- Apply a cap above the day's peak; at/below samples must never release it.
  Verify local date rollover clears it. Separately test cancel, replacement,
  invalid time, automatic-off, group/fixture manual, safe-off and reboot.

## Timed fixed: full hold/return

- Stage 35% and 0.25 hours; Start. Record activation/deadline and confirmation.
  Allow the full 15-minute monotonic duration to pass; the seasonal target
  changes in the background while this fixture stays fixed. The other fixture
  in a shared group must keep following the curve.
- Verify expiry requests the current automatic target within the evaluation
  interval (10 seconds), subject to documented dispatcher timing. Separate the
  request time from eventual physical completion/readback.
- Repeat with 0%, a level above the permanent calibrated limit, and the
  requested two-hour hold. Disconnect HA during a hold; the controller still
  expires it. Exercise a wall-clock change independently of elapsed duration.
- Start again during a write, including the same level, then replace with daily
  maximum. Cancel/expire during an in-flight write. Complete/fail that old
  write; its target must never return to the pending queue and its readback
  must not confirm the new request. Repeat manual, automatic-off, safe-off,
  loss of valid time and reboot interruptions.
- Try invalid action settings through an API/test client: 0.3 or 1.1 hours,
  out-of-range values and invalid calibration/automatic preconditions. Capture
  rejection and prove the active mode/deadline/request were not replaced.

## BLE failure and readback cases

Disconnect/power off the lamp during correction and return. Verify bounded
retries and the recovery interval; the other fixture must progress. Restore
power and capture fresh confirmation. Capture no response, mismatched response,
and a response arriving after a mode change but before the obsolete transaction
ends. These must not indicate confirmation of the latest request. A subsequent
current-generation transaction must provide the confirmation.

The lamp protocol provides no echoed software request token. Generation checks
reject responses belonging to an obsolete active transaction, but cannot prove
provenance of a delayed unsolicited notification during a newer readback window.
Retain that case in the bench report; confirm response ordering on actual lamps
and do not interpret freshness alone as matching output (also compare levels).

## Completion record

For each requirement acceptance criterion 1–8, link a timestamped trace and
record pass/fail, observed requested/completed/reported sequence, timing and any
retest. Attach baseline Gate A results. Only then update the T23 checkbox and
implementation status to complete. Record failed cases as defects, not waivers.
