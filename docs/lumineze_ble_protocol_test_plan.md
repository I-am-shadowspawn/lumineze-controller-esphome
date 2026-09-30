# LuminEZE BLE Protocol Manual Test Plan

## Purpose

This plan defines repeatable app-driven tests for resolving the open questions
in [the protocol findings](lumineze_ble_protocol_findings.md). Each test
changes one protocol-relevant setting at a time, records the app's visible
state, and captures the Android Bluetooth HCI snoop log through an ADB
bugreport.

Run the tests in order. The early cases target current uncertainties in cycle
selection, schedule record count, time encoding, and brightness encoding.
Later cases expand coverage to persistence, record limits, and interactions.
Do not infer a field meaning from one changed packet if the app also changed
other settings in the same test.

## Capture setup and handling

1. Use the same Android phone, app version, LED device, and firmware for a
   comparison series. Record the phone model/Android version, app version,
   lamp model/firmware, local time zone, and whether the lamp was already
   paired.
2. Enable **Developer options > Enable Bluetooth HCI snoop log**. Follow the
   Android version's prompt to restart Bluetooth or reboot if requested.
   Confirm that Bluetooth is enabled and the app can connect to the lamp.
3. Use a stable test environment: keep the phone near the lamp, avoid other
   BLE apps/devices during a run, and do not change lamp power or phone
   connectivity unless the test explicitly calls for it.
4. Establish a known state in the app before each case. Where practical, open
   the device page and allow it to finish connecting and reading its current
   state before making the single planned change.
5. Perform only the steps listed for that case. Wait for the app to finish
   sending the setting and for any visible save/confirmation indication.
   Reopen or refresh the relevant page to trigger a device readback if the
   app supports it. Do not make another protocol-setting change before the
   bugreport is generated.
6. Generate a separate bugreport for each independent test case after the
   final readback/confirmation. Keep the complete bugreport ZIP as the source
   artifact; record its name and the visible app result in the case log.
   Example command (use a fresh filename for each case):

       adb devices
       adb bugreport protocol-test-C1-cycle-1-2026-09-30.zip

   Use a unique file name for every report, substituting the case ID and
   current date. If ADB is unavailable, use the Android bugreport function and
   retain the original archive unchanged.
7. If a test compares a baseline and a changed state, capture a baseline
   report first, then make only the planned change and generate a second
   report. Pair the reports by case ID. Do not combine several unrelated
   cases in one report.
8. Store bugreports privately. They may contain device identifiers,
   notifications, account information, location, and network data. Share only
   the extracted Bluetooth snoop file and the minimum sanitized metadata
   needed for analysis.
9. After starting a bugreport, make no further app changes until ADB reports
   that report generation has completed. The snoop trace can accumulate
   earlier actions; record the wall-clock time immediately before and after
   every planned app action so the relevant interval can be identified.

Bugreport timing matters: generate it immediately after the app's write and
readback, before changing to another test state. A report made before the
write cannot show it; a report made after further changes makes attribution
ambiguous. If no write/readback appears in the extracted snoop, repeat the
case after confirming HCI snoop logging is enabled and the app actually
connected.

## Case record template

For every report, record:

| Field | Value |
| --- | --- |
| Case ID and sequence | |
| Bugreport ZIP filename | |
| Date/time and time zone | |
| Phone / Android version | |
| App version | |
| Lamp model / firmware | |
| Starting app state | |
| One setting changed | |
| Exact action and selected value | |
| Save/confirmation shown | |
| Readback/refresh result | |
| Expected BLE command family | |
| Notes / deviations | |

When analyzing, extract the `btsnoop_hci.log` from the bugreport and preserve
the original ZIP. Record the ATT frame number, timestamp, opcode, handle, and
full value for each relevant `02 F1`, `02 F0`, `03 0F`, `03 F0`, and `03 F1`
packet. Compare full packets, but distinguish command payload bytes from
padding, transport framing, and any trailing checksum/flags not yet decoded.
The archive path varies by Android version; search its file listing for
`btsnoop_hci.log` rather than assuming a fixed internal path.

## Phase 1: Resolve current open questions

### 1. Establish an empty-schedule baseline

**Question:** Does an empty custom schedule reliably read back with a zero
record count, and what operating-state selector is present alongside it?

1. Select the UV lamp and connect in the app.
2. Select the known empty custom schedule, without changing its operating
   mode.
3. Refresh/reopen the schedule and operating-state pages so the app queries
   current values.
4. Record the displayed mode, selected cycle, and number of custom
   timepoints.
5. Generate report `S0-empty-baseline`.

**Expected evidence:** `03 0F` followed by a `03 F0` readback with zero
records; capture the associated `02 F0` state response if present.

### 2. Map built-in cycle selectors

**Question:** Are selector values `01` and `02` stable mappings for Cycle 1
and Cycle 2, what value represents Cycle 3, and what is selector `00` in
automatic mode?

Run one report per selected state. Before each case, reconnect and read the
current mode/cycle; then change only the cycle selection, wait for completion,
refresh the state, and generate the report.

| Case | App action | Record |
| --- | --- | --- |
| `C1-cycle-1` | Select Auto Cycle 1 | `02 F1` write and `02 F0` readback |
| `C2-cycle-2` | Select Auto Cycle 2 | `02 F1` write and `02 F0` readback |
| `C3-cycle-3` | Select Auto Cycle 3 | `02 F1` write and `02 F0` readback |
| `C0-auto-default` | Select the app's default/unspecified Auto option, if it exists | Whether selector `00` is sent/read back |

Do not treat the app's display label alone as proof of the stored selector;
prefer matching write and readback. If there is no default/unspecified Auto
option, mark that case unavailable rather than substituting another setting.

### 3. Test built-in cycle versus custom-schedule interaction

**Question:** Does a non-empty custom schedule affect output while a built-in
cycle is selected, or are they mutually exclusive modes?

1. Create or retain one simple custom schedule with two timepoints and note
   the displayed values.
2. Select Cycle 1, refresh/read back both operating state and schedule, then
   generate `I1-cycle-1-with-custom`.
3. Repeat for Cycle 2 and Cycle 3, generating `I2-cycle-2-with-custom` and
   `I3-cycle-3-with-custom`.
4. Select the custom schedule mode, refresh both states, and generate
   `I4-custom-selected`.

Record whether each cycle-selection action changes schedule count/content,
whether custom selection changes the operating-state selector, and whether
the lamp's observed output follows the built-in cycle or custom points. Keep
the schedule identical across cases. Do not infer output behavior from
commands alone when physical lamp behavior can be observed.

### 4. Confirm custom schedule record-count byte

**Question:** Is the byte after the observed `02` marker the record count for
all supported counts, including one record?

Create separate schedule states with exactly 0, 1, 2, and 3 timepoints.
For each count, refresh/read back the schedule and generate one report:

| Case | Required custom points |
| --- | ---: |
| `N0-zero` | 0 |
| `N1-one` | 1 |
| `N2-two` | 2 |
| `N3-three` | 3 |

Use distinct but simple values and record the UI values. Capture the
`03 F1` write (if any) and the subsequent `03 F0` response. Verify that the
count byte changes as `00`, `01`, `02`, `03`; do not assume the constant
preceding `02` is understood. If the app sends no write for a count because
that is already the stored state, first move to a different count, then make
the target change and capture it.

### 5. Decode time fields independently

**Question:** Which bytes encode hour and minute, and are they binary,
packed, offset, reversed, or another representation?

Use one schedule point at a fixed brightness that is not zero. Keep the
number of points, brightness, and all other settings constant. Create a
baseline report, then change only the point time for each case below and
generate a new report immediately after readback:

| Case | Timepoint | Comparison purpose |
| --- | --- | --- |
| `T0800` | 08:00 | Baseline hour/minute |
| `T0801` | 08:01 | Minute increment |
| `T0830` | 08:30 | Minute range |
| `T0900` | 09:00 | Hour increment |
| `T1000` | 10:00 | Second hour increment |
| `T1200` | 12:00 | Midday / high bit boundary |
| `T2208` | 22:08 | Compare with observed `96 09` |
| `T2359` | 23:59 | End-of-day boundary |
| `T0000` | 00:00 | Midnight / day wrap |

For each time report, compare the same record's first two bytes and check
whether a `03 F0` response echoes the write. The known `22:08 -> 96 09`
association is a reference point, not proof of byte order or encoding. Only
claim a decoded formula after it predicts all sampled values, including
midnight and 23:59.

### 6. Resolve brightness encoding and the 50% discrepancy

**Question:** Does the third record byte directly encode percent, and why was
50% previously observed as `0x2E`?

Use a single timepoint fixed at 12:34 (or another chosen value) and change
only brightness. Generate a separate report for each value; read back after
each write:

| Case | Brightness |
| --- | ---: |
| `B0` | 0% |
| `B1` | 1% |
| `B10` | 10% |
| `B25` | 25% |
| `B49` | 49% |
| `B50` | 50% |
| `B51` | 51% |
| `B75` | 75% |
| `B99` | 99% |
| `B100` | 100% |

Keep the same schedule mode, timepoint, count, and device. Compare both
`03 F1` and `03 F0`; determine whether the record's third byte follows the UI
value, whether the app transforms it, or whether the value is in a different
field. The existing `0% -> 00` and `100% -> 64` observations should be
reproduced in this same series. If the `50%` result is still `2E`, repeat
`B50` after restarting the app and reconnecting without changing firmware or
other settings.

### 7. Determine whether writes persist and when they commit

**Question:** Is a schedule write persistent immediately, only after a later
action, or after an explicit commit?

1. Create a recognizable one-point schedule that differs from the current
   schedule and capture its write and readback as `P1-write-readback`.
2. Without changing another setting, disconnect from the lamp normally.
   Reconnect and query the schedule; generate `P2-normal-reconnect`.
3. Repeat the change, then close/force-stop the app immediately after the
   write appears to finish, without issuing another schedule command. Reopen,
   reconnect, read the schedule, and generate `P3-app-stop-reconnect`.
4. Only if safe and practical, repeat with an immediate lamp power cycle
   after the app reports completion. Reconnect, read back, and generate
   `P4-power-cycle-readback`.

Record whether the point survives each boundary and whether an extra command
appears between write and readback. Do not power-cycle during an in-flight
write unless that is the explicit test condition.

## Phase 2: Expand protocol knowledge after the open questions

### 8. Expand time and brightness coverage

After the phase 1 encodings are reproducible:

1. Test additional time boundaries: 00:01, 06:00, 18:00, and 23:00.
2. Test brightness values around any observed rounding or encoding
   transition, especially near 0%, 50%, and 100%.
3. Repeat selected points on a second LED device, if available, and record
   firmware version. Keep device-specific differences separate from a
   universal protocol rule.
4. Test whether record order in the payload follows entered order or
   chronological order by entering two points in reverse time order. Read
   back the result and note whether the app or lamp sorts it.

Create a new report for every changed value or ordering case. Use one variable
per report and restore the baseline between cases.

### 9. Determine limits, duplicates, and validation

1. Add points one at a time until the app rejects another point or the
   schedule reaches its apparent maximum. Generate a report at each newly
   accepted count and one after the first rejected attempt.
2. Try two points at the same time with different brightness, then exact
   duplicate points. Record app validation, transmitted records, and
   readback.
3. Try boundary values 00:00 and 23:59, and brightness 0% and 100%, in
   separate controlled cases.
4. Do not send malformed packets or use a custom BLE client for this manual
   plan; observe app validation and naturally generated commands only.

### 10. Characterize operating-state fields beyond cycle selection

Use reports with one changed control at a time:

1. Set Manual at 0%, 1%, 50%, and 100% and capture each `02 F1` write and
   `02 F0` readback.
2. Set Auto Cycle 1 and change no other setting; compare with manual packets
   to identify fields retained across mode changes.
3. Repeat the cycle mapping cases after app restart and lamp reconnect.
4. If the app exposes any additional operating modes, test each as a separate
   report and do not assign field names until the app action and readback
   agree.

### 11. Check related commands and response behavior

After schedule and operating-state fields are understood:

1. Compare `03 0F` queries with their `03 F0` responses for each schedule
   count and after reconnect.
2. Note whether `03 F1` uses ATT Write Request or Write Command, whether a
   protocol-level acknowledgement follows, and the delay until readback.
3. Compare initialization and clock-sync traffic across fresh connection,
   reconnect, and app restart. Change only one lifecycle condition per case.
4. Keep any unexplained trailing bytes as unknown fields. Build a byte
   inventory across captures before assigning checksum, flags, or padding
   meanings.

## Reporting conclusions

For each test series, update
`lumineze_ble_protocol_findings.md` with:

- the controlled app action and device/firmware;
- report filename and relevant frame numbers;
- observed write and readback bytes;
- conclusion and confidence;
- alternative explanations and remaining tests.

Use **confirmed** only when the app action is controlled, the relevant packet
changes consistently, and readback or repeat testing supports the mapping.
Use **high confidence** for a repeatable association without complete
encoding/firmware coverage. Keep findings labeled **hypothesis** when only
one packet or a user-interface label supports the interpretation.
