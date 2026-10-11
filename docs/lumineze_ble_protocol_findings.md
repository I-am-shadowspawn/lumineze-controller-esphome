# LuminEZE BLE Protocol Reverse Engineering Findings

## Scope

**Latest review:** 11 October 2026. The case-level review is in
[manual log review](lumineze_ble_protocol_log_review.md), with full ATT values
in `lumineze_ble_protocol_packet_evidence.csv` and original-file hashes/timing
in `lumineze_ble_protocol_capture_inventory.csv`. The case CSV distinguishes
analysis completion from experimental success. Historical sections below
retain their original capture context; newer findings supersede claims of a
constant schedule marker or a universal cycle mapping where stated.

This document summarises the current reverse-engineering state of the
LuminEZE BLE protocol based on captures from the official phone
application and comparison with the existing ESPHome implementation.

The goal is to separate:

-   **Proven observations**: behaviour directly observed in BLE captures
    or confirmed by controlled changes.
-   **Suspicions / hypotheses**: interpretations that fit the evidence
    but require further testing.
-   **Remaining tests**: experiments required to close the gaps.

------------------------------------------------------------------------

# Proven Observations

## 11 October review: repeated cycle and empty-bank evidence

All 30 supplied files are exact cumulative prefixes of the latest snoop
capture. Only newly appended packets count as new evidence. Peer-address
filtering separates the documented JungleDawn 39W from another lamp visited
in early snapshots. The recorded app is V1.1.4; lamp firmware is unspecified.

Cycle 1 = selector `00` is supported by actual write frame 127870 and later
readback 128749, then repeated by write 138105 and readback 138541 in the next
snapshot. Cycle 2 = `01` is supported by write 129312/readback 130088 and
repeat writes 138602/138724 followed by readback 139212 in the next snapshot.
These are same-DUT observations. They do not establish a universal mapping or
erase the historical `01`/`02` observation from a different capture context.

Schedule query `03 0F 06` returns `03 F0 06 00` repeatedly, while query bank
`02` returns `03 F0 02 01 8B 0A 00`. The field at byte 2 is therefore not a
constant `02` marker. It is associated with the queried schedule bank/selector;
custom Cycle 5 in the notes corresponds to `06` in this session. The count
at byte 3 is zero for bank 06 and one for bank 02. Empty-bank evidence is
bank-specific, not proof that the lamp stores no custom points anywhere.

The power-reset capture shows a retained operating selector after the
operator-reported resets, but lacks recorded power boundaries and custom-bank
readback. The app syncs clock before querying state, so onboard clock retention
is unresolved. The named S0 cycle-repeat file is missing; related actions are
present in the later cumulative C1 snapshot but cannot complete the intended
read-only comparison. Both gaps have explicit retest rows in the case CSV.

## Additional Capture: Built-In Cycles and Empty Custom Schedule

The `btsnoop_hci.log` capture records the user-described controlled sequence:
default Cycle 2, Cycle 1, Cycle 2, a custom schedule with no timepoints, then
Cycle 1.
ATT writes to handle `0x0011` carry the commands; notifications on handle
`0x000e` carry operating-state and schedule responses. Frame numbers below are
from this capture, and times are seconds from its start.

### Operating-state cycle selector

`02 F1` writes retain a third payload byte (the fifth byte of the full
command) that changes with the selected cycle, independently of the
manual/automatic byte:

| Capture evidence | Bytes after `02 F1` | Observation |
| --- | --- | --- |
| Frame 429, 29.749 s | `00 00 02` | Manual state, zero level, selector `02` |
| Frame 507, 33.798 s | `01 00 02` | Automatic state, selector remains `02` |
| Frame 4213, 2131.808 s | `01 00 02` | Automatic state, selector `02` |
| Frame 2893, 1532.768 s | `01 00 01` | Automatic state, selector `01` |
| Frame 4420, 2177.286 s | response `02 F0 01 00 01 ...` | State readback reports selector `01` |

The controlled UI sequence identifies selector `02` as Cycle 2 and selector
`01` as Cycle 1. The selector is distinct from the auto/manual field; it is
not a brightness byte. A `00` selector also occurs in manual state (frames
2880 and 2884), but this capture does not establish what `00` means when
automatic mode is active.

### Schedule record count

The third byte after the command header is now strongly indicated to be the
schedule record count; the preceding `02` remains constant in the observed
schedule messages:

| Capture evidence | Bytes after command | Observation |
| --- | --- | --- |
| Frame 438, 29.843 s (`03 F0`) | `02 02 88 2E 64 93 2E 4A ...` | Response contains two three-byte records |
| Frame 4230, 2169.057 s (`03 F1`) | `02 03 88 2E 2E 93 2E 00 96 09 64 ...` | Write contains three three-byte records |
| Frame 5565, 2512.055 s (`03 F0`) | `02 00 00 ...` | Readback reports zero records |

In these examples the first byte after `03 F0`/`03 F1` is `02`, and the next
byte matches the number of records: `02`, `03`, or `00`. The application
sequence identifies the zero-record readback with the custom schedule having
no timepoints. This corrects the earlier tentative interpretation that the
first `02` itself was the record count.

The observed three-record write changes the message content relative to the
two-record response. The individual three-byte record fields are still not
decoded; their presence alone does not establish that they are time,
brightness, or a particular schedule-point type.

### What the capture establishes

- Built-in Cycle 1 and Cycle 2 selection is represented by different values
  (`01` and `02`) in the operating-state command and state response.
- Changing manual/automatic state does not itself change the cycle selector;
  `00 00 02` followed by `01 00 02` retains Cycle 2.
- The schedule record count is most consistently located immediately after
  the constant observed `02` marker.
- A custom schedule can be read back with zero records. Built-in cycle
  selection and custom schedule contents are separate state dimensions in
  these messages; a zero-record custom schedule does not imply a missing or
  invalid built-in cycle.

The capture does not prove whether every lamp firmware version uses these
same selector values, what selector `00` means in automatic mode, or whether
the custom schedule is applied while a built-in cycle is selected.

## Additional Manual Test Captures: Empty Schedule and Cycle 1/2

The four `manual_test_resources/protocol-test-*_2026-10-10_btsnoop_hci.log`
files are cumulative snapshots of the same HCI snoop history, not isolated
per-case traces. They all begin on 2026-10-08; their latest packet times are
14:50:27 (`pre_test`), 14:57:01 (`s0-empty-baseline`), 15:03:53
(`C1-cycle1`), and 15:11:58 (`C2-cycle2`) on 2026-10-10. Attribute a packet
to a test using its timestamp and the operator's action notes, not merely the
filename. The snapshots contain earlier, unrelated device activity too.

### Empty custom schedule

In the `s0-empty-baseline` time window, the app read and rewrote operating
state, then queried the schedule:

| Frame / time | Value | Observation |
| --- | --- | --- |
| 127663 / 14:54:08.062 | notification `02 F0 01 51 06 ...` | State response |
| 127664 / 14:54:08.072 | write `02 F1 01 51 06 ...` | State write |
| 127665 / 14:54:08.081 | write `03 0F 06 ...` | Schedule query |
| 127673 / 14:54:08.163 | notification `03 F0 06 00 ...` | Zero records reported after the `06` field |

This supports the user-reported empty custom schedule: the response's record
count is `00`. However, the preceding field is `06`, not the `02` seen in
earlier captures, so the earlier claim that this field is a constant marker
is not universal. Its meaning remains unknown. The response confirms a
zero-record readback for this session; it does not decode the `06` field.

An earlier packet in the same cumulative history (frame 125947 at 14:51:41)
is `03 F0 02 01 8B 0A ...`. It may represent a one-record response, but it
precedes the explicitly described empty-schedule action and is not isolated
to a controlled one-entry test.

### Built-in Cycle 1 and Cycle 2

On the test device identified in the notes as `2B:80:04:04:B2:34`, the
operator reported Cycle 1 selected and visible after switching devices,
returning, and reopening the app:

| Frame / time | Value | Observation |
| --- | --- | --- |
| 128749 / 15:01:03.024 | notification `02 F0 01 51 00 ...` | Auto state response |
| 128750 / 15:01:03.031 | write `02 F1 01 51 00 ...` | State write |

For Cycle 2, the capture first shows the existing Cycle 1 value, then a
selector change, followed by a readback after reopening/rescanning:

| Frame / time | Value | Observation |
| --- | --- | --- |
| 129267 / 15:05:09.992 | notification `02 F0 01 51 00 ...` | Existing state response |
| 129268 / 15:05:10.000 | write `02 F1 01 51 00 ...` | Repeated existing state |
| 129312 / 15:05:15.179 | write `02 F1 01 51 01 ...` | Third payload byte changes from `00` to `01` |
| 130088 / 15:09:07.309 | notification `02 F0 01 51 01 ...` | Readback retains the changed value |
| 130089 / 15:09:07.321 | write `02 F1 01 51 01 ...` | App repeats the read state |

The user reports the app still displayed 81%, Auto, and Cycle 2 after
reopening. `0x51` is consistent with 81 decimal in the second payload byte;
the third payload byte is associated with the selected cycle in these
controlled actions. In this capture, Cycle 1 is associated with `00` and
Cycle 2 with `01`. This conflicts with the separate capture summarized above
(Cycle 1 = `01`, Cycle 2 = `02`), so the selector mapping must not be treated
as universal until device/firmware and exact UI transitions are compared in
a clean, controlled repeat.

The operator also noted apparent time/brightness points for each built-in
cycle. None of the four supplied logs contains a `03 F1` schedule write, so
those notes do not establish custom schedule contents or encoded records.
The traces show state and schedule query/readback traffic, not proof that
built-in cycle curves are transmitted as custom records or that custom
records affect output during a built-in cycle.

### Evidence limits and follow-up

- The pre-test snapshot ends before the described test actions and does not
  establish a protocol baseline.
- The empty-schedule count is evidenced by frame 127673, but the preceding
  `06` field needs comparison with controlled schedule reads on the same
  device.
- Cycle 1 and Cycle 2 selection/readback are supported on the test device,
  but their values conflict with the earlier capture. Record model,
  firmware, app version, and the exact selected label in a fresh repeat.
- Cycle 3, a separate automatic default/unspecified option, the interaction
  with a non-empty custom schedule, and physical output behavior remain
  untested. Selector `00` is associated with Cycle 1 in this test, not proven
  to be a default selector.
- To avoid ambiguity from cumulative snoop history, record action timestamps
  and extract only the interval for each case. Preserve the original
  artifacts and verify a post-action `02 F0` readback.

## Additional Capture: Third Custom LED Window at 22:08, 0%

In the LED-device capture, the user added a third timepoint to the custom
schedule and set it to 22:08 at 0% brightness. Two `03 F1` writes on handle
`0x0011` show the record being edited:

| Frame | Time from capture start | Schedule payload after `03 F1` | Observation |
| --- | ---: | --- | --- |
| 4230 | 2169.057 s | `02 03 88 2E 2E 93 2E 00 96 09 64 ...` | Three records; third record is `96 09 64` |
| 4234 | 2170.649 s | `02 03 88 2E 2E 93 2E 00 96 09 00 ...` | Same records and encoded time; third record's last byte changes to `00` |

Within the schedule record block, frame 4234 changes the third record's final
byte from `0x64` (100 decimal) to `0x00`, while retaining the preceding
`96 09` bytes. Other trailing bytes outside the three records also differ.
Together with the user-confirmed UI value, this is strong evidence that the
third byte of each three-byte record is the brightness level, and that
`0x00` represents 0% (off). The record `96 09 00` is associated with the
newly added 22:08 / 0% window.

This controlled same-record comparison is more informative than the earlier
50% example: that earlier capture showed `0x2E` for a UI value of 50%, so
brightness encoding is not yet fully characterized. The new evidence supports
direct encoding at 0% and 100%, but does not establish the mapping for
intermediate values.

The first two bytes `96 09` are associated with 22:08 in this controlled
change, but their encoding is still unknown. The capture contains a later
`03 0F` schedule query (frame 4421) but no corresponding `03 F0` schedule
response after the write; therefore the final setting is evidenced as sent by
the app, not independently confirmed by a post-write lamp readback in this
capture.

------------------------------------------------------------------------

## BLE Transport

  -----------------------------------------------------------------------
  Item                                Observation
  ----------------------------------- -----------------------------------
  BLE service                         `FFF0`

  Command characteristic              `FFF2`

  Protocol frame size                 Generally 16-byte command frames

  Existing ESPHome compatibility      Manual state changes already use
                                      the same protocol family
  -----------------------------------------------------------------------

The phone app communicates using proprietary GATT commands rather than
standard lighting profiles.

------------------------------------------------------------------------

# Command Families Identified

The protocol appears to use the first byte as a command family selector.

## Initialization

Observed:

    05 F0 00 01 02 03 04 00 00 00 00 00 00 00 00 50

Response:

    05 F0 01 01 02 03 04 00 00 00 00 00 00 00 00 50

Status:

-   Confirmed as a session/device initialisation exchange.

------------------------------------------------------------------------

# Clock Synchronisation

Observed command:

    01 0F EA 07 03 09 1E 15 20 34 ...

Interpretation:

    01 0F
    year
    weekday
    month
    day
    hour
    minute
    second

Evidence:

-   Values matched the phone's current date/time during capture.

Status:

-   Clock upload from phone to lamp is confirmed.
-   The timezone basis (local wall time versus UTC), sync trigger conditions,
    and clock persistence through disconnects or power cycles are not yet
    established. The observed field sequence needs repeat comparison across
    connection lifecycles and a controlled phone-time-zone change.

------------------------------------------------------------------------

# Manual / Auto Operating State

Command family:

    02 F1

Observed examples:

Manual 0%:

    02 F1 00 00 02 ...

Auto mode:

    02 F1 01 00 02 ...

Confirmed:

  Byte     Meaning
  -------- -------------------------
  byte 2   manual/auto selection
  byte 3   manual brightness level

Current interpretation:

    00 = manual
    01 = automatic

The next payload byte also varies and is associated with the selected built-in
cycle in the new capture; earlier command examples omitted this field.

This is strongly supported by controlled UV lamp testing.

------------------------------------------------------------------------

# Schedule Protocol

Command family:

    03 xx

Observed:

Query:

    03 0F ...

Response:

    03 F0 ...

Write:

    03 F1 ...

Confirmed:

-   The app queries stored schedules using `03 0F`.
-   The lamp responds with `03 F0`.
-   Schedule writes use `03 F1`.

------------------------------------------------------------------------

# Custom Schedule Entry Discovery

Controlled LED test:

Original:

    08:48 100%

Changed:

    08:47 50%

Observed write changes:

    88 2E 64
    88 2F 64
    88 2F 2E
    88 2E 2E

Confirmed:

-   The schedule payload changes when time or brightness changes.
-   The three-byte groups are likely schedule records.

Observed structure:

    03 F1
    02 <record count>
    <record 1>
    <record 2>
    ...

In this capture, the first `02` remains constant while the following byte
matches the observed record count, including zero, two and three. The meaning
of the constant marker remains unknown.

------------------------------------------------------------------------

# Built-in Cycle and Custom Schedule State

The capture shows that the selected built-in cycle and custom schedule
contents have separate fields/commands:

-   Cycle selection is carried in the operating-state exchange (`02 F1` /
    `02 F0`).
-   Custom schedule records are read/written through `03 F0` / `03 F1`.
-   The lamp can report automatic mode with a built-in cycle selected and a
    custom schedule record count of zero.

This supports treating built-in cycle selection and custom schedule storage as
distinct protocol state. It does not prove whether stored custom records affect
output while a built-in cycle is selected.

------------------------------------------------------------------------

# Suspicious / Unconfirmed Interpretations

These items fit the evidence but are not yet proven.

## Schedule Record Format

Hypothesis:

    03 F1
    02 <record count>
    record1
    record2
    ...

Possible entry:

    byte 0 = time/hour encoding
    byte 1 = minute encoding
    byte 2 = brightness

Evidence:

-   The capture shows a constant `02` marker followed by counts of `00`,
    `02`, and `03`.
-   Three-byte record groups follow the count.

Unknown:

-   Exact encoding of hour.
-   Exact encoding of minute.
-   Whether additional flags exist.

------------------------------------------------------------------------

## Brightness Encoding

Observed:

    100% -> 0x64
    0%   -> 0x00

but:

    50% -> 0x2E

The controlled 0% change from frame 4230 to 4234 changes the third record's
final byte while retaining its first two bytes, supporting that final byte as
the brightness field. The 0% and 100% observations match direct percentage
encoding, but the earlier 50% observation does not. This suggests:

-   brightness may not always equal decimal percentage;
-   a transformation or offset may exist;
-   or the byte identified may not be the brightness field.

Intermediate levels and the earlier 50% discrepancy need a controlled
single-variable repeat with schedule readback.

------------------------------------------------------------------------

## Time Encoding

Observed:

    08:48 -> byte pattern containing 0x2E
    08:47 -> byte pattern containing 0x2F

The relationship is not yet understood.

Possibilities:

-   reversed minute count;
-   encoded offset;
-   packed time field;
-   bitfield.

------------------------------------------------------------------------

## Built-in Cycle Selection

Observed:

    02 F1 01 00 <profile>

may select a factory light-cycle profile.

Evidence:

-   Under the controlled sequence, Cycle 1 and Cycle 2 use selector values
    `01` and `02` respectively.
-   The selector is returned in the `02 F0` operating-state response.
-   Manual/automatic state changes can retain the same selector.

Remaining uncertainty:

-   The meaning of selector `00` in automatic mode is unknown.
-   Whether the selector is stable across lamp firmware versions is untested.
-   The interaction between a selected built-in cycle and non-empty custom
    schedule contents is not established.

------------------------------------------------------------------------

# Remaining Tests Required

## 1. Decode Time Encoding

Create schedules changing only time:

    08:00
    08:01
    08:30
    09:00
    10:00
    12:00
    23:59

Capture each write.

Goal:

Determine:

-   hour location;
-   minute location;
-   encoding method.

------------------------------------------------------------------------

## 2. Decode Brightness Encoding

Change only brightness:

    0%
    1%
    10%
    25%
    50%
    75%
    99%
    100%

Capture each write.

Goal:

Determine whether:

-   value is direct percentage;
-   scaled value;
-   transformed value.

The new capture associates 0% with `00` and shows the earlier 100% record as
`64`, but the 50% observation remains inconsistent with direct percentage
encoding. Repeat intermediate levels at the same timepoint and verify with a
post-write `03 F0` readback.

------------------------------------------------------------------------

## 3. Confirm Schedule Entry Count

Create:

-   zero entries;
-   one entry;
-   two entries;
-   three entries.

Check whether:

    03 F1 xx

changes with entry count.

The new capture indicates that the byte after the constant `02` marker is the
entry count. Repeat with controlled zero-, one-, two- and three-entry writes
and verify each with `03 F0` readback.

------------------------------------------------------------------------

## 4. Decode Built-in Cycles

On UV lamp:

Test:

    Manual
    Auto Cycle 1
    Auto Cycle 2
    Auto Cycle 3

Capture only the transition.

Goal:

Confirm the selector mapping and readback for:

    02 F1 byte4

including Cycle 3 and selector `00`. Also repeat the empty-custom-schedule
readback after each cycle selection and test whether custom records affect
output when a built-in cycle is selected.

------------------------------------------------------------------------

## 5. Determine Schedule Commit Behaviour

Test:

-   modify schedule;
-   disconnect immediately;
-   reconnect;
-   read schedule.

Goal:

Determine whether:

-   writes are immediately persistent;
-   a commit command exists.

------------------------------------------------------------------------

# Current Protocol Map

    05 F0
        Initialisation

    01 0F
        Set clock

    02 0F
        Read operating state

    02 F0
        Operating state response

    02 F1
        Write operating state
            byte2:
                00 manual
                01 auto

            byte3:
                manual brightness

            byte4:
                Conflicting observations:
                    one capture: 01 = Cycle 1, 02 = Cycle 2
                    2026-10-10 test device:
                        00 = Cycle 1, 01 = Cycle 2
                Resolve against device/firmware and controlled readback

    03 0F
        Read schedule

    03 F0
        Schedule response
            byte2: observed 02 and 06; meaning unresolved
            byte3: candidate record count (observed 00, 02, 03 in
                   controlled examples; 01 occurs in an earlier,
                   uncontrolled response)

    03 F1
        Write custom schedule
            byte2: observed constant marker 02 in earlier captures;
                   not yet compared across modes/devices
            byte3: record count

------------------------------------------------------------------------

# Confidence Summary

  Area                       Confidence
  -------------------------- -------------------
  BLE transport              Confirmed
  Initialisation command     Confirmed
  Clock synchronisation      Confirmed
  Manual/auto mode byte      High confidence
  Schedule command family    Confirmed
  Schedule record count      High confidence (capture shows 0, 2 and 3)
  Built-in cycle selector    High confidence as a field; value mapping conflicts
  Schedule entry size        Medium confidence
  Time encoding              Unknown
  Brightness encoding        Unknown
