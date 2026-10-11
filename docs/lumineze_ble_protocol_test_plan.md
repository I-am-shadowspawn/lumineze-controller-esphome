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
   current date. For these supplied logs, the operator confirms filename times
   record bugreport request initiation in BST. Record request initiation and
   completion separately from action and last-packet times. If ADB is unavailable, use the Android bugreport function and
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

## Starting a fresh capture window

Generating a bugreport copies diagnostic data; it does not reset the Bluetooth
snoop. Android documents restarting Bluetooth after changing HCI logging. The
current AOSP logger opens a new active file on startup, rotates the previous
file to `.last`, and removes full/filtered snoop files when initialized with
logging disabled. This describes AOSP behavior, **not a verified guarantee on
the Motorola Edge 40 / Android 15 build** used here.

For a new independent case:

1. Save the previous report and close the lamp app.
2. Disable Bluetooth HCI snoop logging in Developer options. Restart Bluetooth
   (off, then on) so the disabled setting takes effect; reboot if the phone
   requires it.
3. Enable full HCI snoop logging, then restart Bluetooth again. Record this
   capture-start time, date and phone time zone before opening the app.
4. Connect only to the DUT, execute the case, record action/readback/end times,
   and generate one uniquely named bugreport. Wait for completion.
5. Inspect the extracted active `btsnoop_hci.log`: its first packet must be
   consistent with the new capture start, and it must contain the connection
   setup and full DUT values. Keep any `.last` file separate; it may contain
   the previous session. If old packets remain, use the fallback below.

Do this between independent cases, **not between a case's write and its
reconnect/force-stop/power-cycle observation**. Restarting phone Bluetooth is
an extra lifecycle intervention: include it in the case notes. For fresh-app
comparisons, follow the case's required app state separately.

### Reliable fallback when the phone retains history

Keep the original report and extracted snoop unchanged. In Wireshark, select
a time window from just before the target connection setup through final
readback, using the recorded start/end timestamps, then export the displayed
packets to a separate derived capture. Preserve connection establishment,
service discovery and MTU traffic needed to decode the full session; filter
the peer/session only after that context is available. Record the source
filename/hash, original frame range, time zone and export filter. Exported
frame numbers will differ from the source.

This creates a clean **analysis window** even when the original bugreport
remains cumulative. Verify it contains every fragmented/reassembled command
and notification before treating it as the case artifact. Taking another
report, closing the app, or clearing `logcat` alone does not establish a fresh
HCI log. Other bugreport sections can retain history even with a fresh snoop.

Sources checked 11 October 2026:
[AOSP Bluetooth capture instructions](https://source.android.com/docs/core/connect/bluetooth/verifying_debugging),
[AOSP snoop logger implementation](https://android.googlesource.com/platform/packages/modules/Bluetooth/+/refs/heads/main/system/gd/hal/snoop_logger.cc),
[Android bugreport documentation](https://developer.android.com/studio/debug/bug-report).

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

### Evidence review: updated 11 October 2026

All 30 supplied files have been reviewed against the case script. They are an
exact cumulative byte-prefix chain, not isolated per-case captures. The
[case-level review](lumineze_ble_protocol_log_review.md),
[case CSV](lumineze_ble_protocol_case_records.csv), packet evidence and hashed
capture inventory preserve the frame-level results and progress. This table
summarizes what the actual experiments establish:

| Planned question | Current evidence | Remaining work |
| --- | --- | --- |
| Empty custom bank | Bank 06 repeatedly reads zero; bank 05 zero-count deletion reads back in N1 | Read-only comparison across built-in/custom selection; one named S0 file missing |
| Cycle selectors | Same-DUT Cycle 1=`00`, Cycle 2=`01`, with repeat independent readback | Firmware/version scope and historical different mapping; Cycle 3/default UI options reported unavailable |
| Built-in/custom interaction | Bank-05 points survive both selector changes; immediate output changes reported | Timed physical observations while staying in each mode; custom page queries also reselect mode |
| Count field | Bank-05 counts 0,1,2,3 have matching later readback | Capacity, duplicates' output precedence, cross-device differences |
| Time bytes | All nine T-series values match `80+hour`, binary minute | High-bit semantics; strict single-point repeat (actual series retained three points) |
| Brightness | Controlled final 0,1,21,50 match decimal bytes | Wider B-series and historical 50% attribution; B10 has no log and achieved 9% |
| Persistence | Custom contents retained across ordinary reconnects | Actual power-loss, force-stop and immediate commit timing |
| App Full power test | Two `04 F0`/`04 0F` pairs; Test control button identified by operator | Timed 0%/100% cycle, return to requested output, command roles and state/bank preservation |
| Clock and transport | Repeated local-BST-compatible clock uploads, 152-byte writes/150-byte responses, ATT Write Command | Controlled timezone/weekday/power tests; trailer semantics |

Each required follow-up is inserted immediately below its parent case in the
CSV with concrete steps. “Reviewed” means the evidence was analyzed, not that
an experiment passed. The coverage follow-up marks 11 redundant runs unnecessary
and two discrepancy-triggered runs unnecessary for current findings; their CSV
results reference reused packets rather than claiming new execution. Other
cases without supplied captures remain explicitly
unreviewed; dates or results are not inferred from planned instructions.
Original historical findings are retained in a separate historical document.

Capture action times from packets and preserve filename/report times separately.
The N3 filename records bugreport request initiation at 18:41:08 BST; its
write occurs earlier at 17:58:38.448 BST. The gap is a delayed report, not an
incorrect filename timestamp.
Record the **actual achieved UI value**, not only the target: the B10 note says
9%, and B1 contains fourteen actual interim writes before final 1%. Newly added
points can send a default 100% before the requested adjustment. Record all
intermediate traffic and conduct tests on the isolated setup in the plan.

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

**Current result:** Bank 06 count zero is independently read at frames
127673 and 136879; bank 05 count zero after deletion is read at 145912. The
byte preceding count follows the queried bank rather than being constant.
The named S0-empty-cycle-repeat capture is absent; related 17:13 actions appear
in the later cumulative C1 log, but do not provide the intended passive bank
comparison. Follow its inserted retest and record when opening a custom page
also writes the operating selector. Do not treat bank 06 being empty as proof
that bank 05 or all custom banks are empty.

### 2. Map built-in cycle selectors

**Question:** What selector values map to Cycle 1, Cycle 2, and Cycle 3 on
each device/firmware, and what is selector `00` in automatic mode?

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

**Current result:** Same-DUT controlled repeats support Cycle 1 selector
`00` and Cycle 2 `01`, with independent state reads in adjacent captures.
Own-file absence of post-write state is filled by later readback and explicitly
referenced in the CSV. Preserve the historical `01`/`02` association as a
separate unresolved device/firmware comparison. Record firmware and exact UI
labels before repeating on another DUT. Cycle 3 and unspecified Auto were
reported unavailable; no mapping is inferred for them.

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

**Current result:** I0 writes 17:31/21% and 17:36/0% to bank 05, read
back in I1. Contents are retained after both built-in selections. The
operator reports immediate 0%↔100% changes for Cycle 1/custom reselection,
but the actions do not observe both future scheduled transitions. I2 has no
recorded physical result. I4 occurs after both point times. The inserted
I1/I2/I4 retests use future points and separate physical observations from
stored contents; keep a built-in mode selected throughout each observation.

### 4. Confirm custom schedule record-count byte

**Question:** Which response/write byte is the record count, and does it
track all supported counts, including one record, when the preceding field
varies?

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
count byte changes as `00`, `01`, `02`, `03`; do not assume the preceding
field is a constant marker (`06` preceded the zero count in the 2026-10-10
empty-schedule response, while earlier captures show `02`). If the app sends
no write for a count because that is already the stored state, first move to
a different count, then make the target change and capture it.

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
| `T2208` | 22:08 | Current `96 08` versus disputed historical `96 09` |
| `T2359` | 23:59 | End-of-day boundary |
| `T0000` | 00:00 | Midnight / day wrap |

For each time report, compare the same record's first two bytes and check
whether a `03 F0` response echoes the write. The historical `22:08 -> 96 09` association is disputed: the reviewed N3
and T2208 captures use `96 08`. The current sampled formula predicts all
nine values, including midnight and 23:59, with independent readback. The
actual series retained three points and reordered them; use the inserted
Manual/Auto follow-up for high-bit investigation. The one-point baseline
is already covered by N1, and the operator confirms no per-point toggle exists.

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

**Current result:** B0 and B1 independently confirm final 0% and 1%.
N1 and all time cases confirm 50% as `32`; I0 confirms 21% as `15`.
The historical 50%/`2E` discrepancy is not reproduced and must not be assumed
a nonlinear rule. B10 has an operator-only 9% result and no capture; its
inserted retest records the actual selected value. B25 onward remain planned
without supplied logs. Do not associate unrecorded UI values with B1's interim
slider packets.

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

### 12. Characterize onboard clock synchronization

**Question:** Which phone time basis is encoded by `01 0F`, when does the app
send it, and does the lamp keep schedule time through reconnects and power
cycles?

1. Record the phone's local date/time, UTC time, time zone, and Android
   automatic date/time setting. On a fresh app-to-lamp connection, capture the
   complete `01 0F` command and compare its year, weekday, month, day, hour,
   minute, and second fields with both local time and UTC.
2. Without changing the phone clock, schedule, or operating mode, capture
   separate reports after a normal disconnect/reconnect and after app
   restart. Record whether `01 0F` is sent, when it is sent relative to
   initialization/state reads, and whether its payload tracks the phone.
3. Capture a baseline with the phone in its current time zone. Change only
   the phone time zone while automatic date/time remains enabled, reconnect,
   and capture a second report. Compare local and UTC values to determine
   whether the command carries local wall time or UTC. Restore the original
   time zone after capturing the changed-zone report; do not manually change
   the phone date/time.
4. After all BLE writes have completed, safely power-cycle the lamp, reconnect,
   and capture whether the app resends `01 0F`. Do not interrupt an in-flight
   write.
5. To confirm that the onboard clock drives schedules, use a one-point
   schedule at a near-future time and observe the physical lamp transition.
   Record phone time/time zone, scheduled time, whether clock sync occurred,
   and observed output. Protocol packets alone do not prove clock accuracy.
6. Compare `01 0F` captures on different natural dates or weekdays to verify
   date/weekday field positions without manually altering the phone clock.

Record full command bytes, frame/timestamp, ATT handle/opcode, local and UTC
times, and the lamp model/firmware. Keep any timezone, weekday, persistence,
or sync-trigger behavior that is not directly shown by repeated captures
unconfirmed.

## Review-driven additional test guidance

- The original “full power reset” case is confirmed as app **Test control >
  Full power test**, pressed twice. Family `04 F0`/`04 0F` appears twice on
  one session. The narrowed retest records one button press, timed physical
  output through the apparent 0%/100% cycle and return to requested level,
  plus before/after state and bank reads. Individual command roles remain
  unknown. Use P4 separately for actual physical power-loss persistence.
- The operator confirms no point enable/disable control exists. Always-set
  `80` is not sufficient to identify an enable flag; investigate Manual/Auto
  mode dependence using the same unchanged custom bank as described below.
- Preserve full 152-byte custom writes and 150-byte responses. Compare the
  trailer at offsets 148 onward separately for time and brightness edits;
  do not guess checksum or record-capacity meanings from padding.
- Preserve record identity through UI sorting. Since the current app sends
  sorted records already, readback alone does not demonstrate lamp-side sorting.
- Schedule query/open actions can also select that bank through `02 F1`.
  Record the state before and after, especially when testing built-in precedence.

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

## Operator-confirmed active-cycle precedence (11 October)

The operator confirms that the cycle selected in the app governs lamp
brightness. The I1 future-transition precedence follow-up is therefore
unnecessary for establishing that operating model. Keep its original steps
as an optional trace protocol. Detailed custom interpolation/transition
timing, exact state readbacks and empty-bank fallback retain their separate
case objectives; no new hardware trace is implied by this confirmation.

## Revised follow-ups after operator clarification (11 October)

- **I4:** sharp scheduled steps and no gradual fading are operator-confirmed.
  No further experiment is required to distinguish step from interpolation;
  the original protocol is optional for precise timing evidence.
- **T0800:** N1 covers the one-point baseline, and no point toggle exists.
  Retire that retest; retain bit `0x80` as unknown.
- **MODE-manual-auto-schedule-bit:** hold Cycle 4/bank 05 and its contents
  fixed, switch Auto -> Manual -> Auto, and capture full state and schedule
  traffic. Confirm state before/after any schedule query; if the query switches
  back to Auto, it cannot establish Manual-mode record bytes. Compare mode
  byte, selector, count, hour high bits and trailers separately. The full
  executable protocol is in the case records. Do not assume the high bit is
  an enable flag or send custom packets to force a comparison.

### Manual/Auto comparison result

The new mode capture isolates `02 F1` byte 2 as Manual `00` / Auto `01`
without changing bank or level. Connecting preserves the prior mode by
operator confirmation; the captured initial Auto read precedes its matching
echo. This does not imply that viewing/selecting another cycle is passive.
No bank read occurs in Manual, so high-bit semantics remain open. The
narrowed `MODE-manual-bank-read-follow-up` checks for a passive UI read;
if the app cannot provide it, record the comparison as unavailable rather
than repeat the already successful mode toggles.

### Third mode capture outcome

Manual-mode schedule reading is now demonstrated; no repeat is needed to
check UI capability. Record hour high bit remains set while mode is Manual,
ruling out a direct current-Auto indicator. Exact bit semantics remain unknown,
and matched Auto bank02 data is not supplied. Lamp-origin83% and22% reads
confirm app refresh of current Manual state; the operator corrected the
final value to22%, matching the wire/readback. Investigate ESP external-change reconciliation with
ESP evidence if requested; do not infer its internal behavior from phone logs.

### Auto/Manual behavioral scope complete

No further retest is required for mode-byte control, retained mode on
connection, current Manual-level refresh or Manual-mode schedule reading.
These conclusions combine captured evidence with explicit operator
confirmation; they do not claim a complete timed trace for every condition.
High-bit semantics remain unknown for future protocol research. The ESP
stale-state observation requires separate ESP investigation if pursued.

### Timezone retry complete (Cyprus)

BST -> Cyprus -> BST clock uploads confirm phone-local wall time, not UTC.
The timezone baseline/shift objectives are covered; retain the empty Perth
attempt as historical evidence and mark the combined retest reviewed.
No additional zone change is needed to establish this sampled rule.
The same bank is now read inManual andAuto with unchanged high bit 80,
completing that comparison without decoding the bit'sunderlying meaning.
