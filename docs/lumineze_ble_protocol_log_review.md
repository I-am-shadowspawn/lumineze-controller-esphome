# Manual capture analysis — 11 October 2026

This review compares the test plan, operator case records and all supplied
binary HCI snoop captures. Analysis progress and outcomes are tracked in
`lumineze_ble_protocol_case_records.csv`. “Reviewed” records analysis completion,
not necessarily a passing experiment. Results distinguish transmitted values,
independent notifications, operator observations and unresolved behavior.

## Evidence and timing method

The 30 files form an **exact byte-prefix chain**, ordered by their last packet,
from the pre-test capture through B1. Every later file contains every byte of
the preceding file plus appended records. They are not isolated cases, even
when named “isolated-repeat”. All start at 8 October 2026 16:12:01.761 BST.
Use the newly appended interval for each report and inspect neighboring reports
for later readback; never count overlapping copies as independent repeats.

`lumineze_ble_protocol_capture_inventory.csv` records original names, SHA256,
frame counts, absolute first/last packet times and newly appended frame ranges.
HCI snoop timestamps are converted to Europe/London (BST, UTC+01:00 on 10 October).
The operator confirmed on 11 October that filename timestamps identify
**bugreport request initiation**, in BST. Packet timestamps identify BLE
actions; the last packet identifies capture end, not necessarily report
completion. Several captures continue about two minutes after request
initiation, consistent with collection continuing during report generation.
The inventory now records initiation separately where filenames include time;
date-only filenames leave that field blank. N3 was requested at 18:41:08
after its 17:58:38.448 write; the difference is not a filename error.

`lumineze_ble_protocol_packet_evidence.csv` preserves full relevant ATT values,
frame numbers, millisecond timestamps, opcode, ATT handle, connection handle,
direction and lengths. Values are scoped to the operator's JungleDawn DUT by
the HCI peer address, not merely an ATT handle; the early captures also visit
another lamp and contain unrelated Bluetooth traffic. Commands use ATT Write
Command `0x52` on `0x0011`; responses are notifications `0x1B` on `0x000E`.
No UI-save confirmation is inferred from a write command. Original files are
preserved unchanged. Extraction used installed `tshark` with `btatt.value`,
frame/timestamp/peer/connection/opcode/handle fields; raw snoop record headers
independently supplied capture bounds and counts.

The operator identifies Motorola Edge 40 / Android 15, app V1.1.4 and JungleDawn
39W, with no lamp firmware version. Device-specific conclusions cannot be
promoted to universal firmware mappings. Full packet values are in the evidence
CSV; tables below show meaningful prefixes and record blocks, not undocumented
trailing bytes.

## First batch: context, empty bank and cycle selection

| Capture/case | Relevant evidence | Conclusion and limits |
| --- | --- | --- |
| `pre_test` | Ends 14:50:27.492; no identified-DUT command | Context only. An unrelated device happens to emit bytes starting `02 F1`; prefix alone is not protocol evidence. |
| `s0-empty-baseline` | 125947: `03 F0 02 01 8B 0A 00`; 125962/127673: `03 F0 06 00` | Bank 02 contains one record; bank 06 is empty. The field before count varies with the queried bank. Second-lamp packets excluded. |
| `C1-cycle1` | 127870 at 14:58:07.197: `02 F1 01 51 00`; 128749 at 15:01:03.024: `02 F0 01 51 00` | Actual selector change and later readback support Cycle 1 = `00` on this DUT. 128750 is an app echo after readback. |
| `C2-cycle2` | 129312 at 15:05:15.178: `02 F1 01 51 01`; 130088 at 15:09:07.309: `02 F0 01 51 01` | Cycle 2 = `01` retained after reconnect. The visit to another lamp must not be mixed into this mapping. |
| `baseline_pretesting` | New frames 130171–135115, no relevant DUT commands | Snapshot does not establish a fresh operating baseline; earlier C2 packets are inherited. |
| `full-power-reste` | 135375 at 17:01:46.418: `02 F0 01 51 01`; 135382/135384 and 135388/135390: `04 F0` / `04 0F` command pairs | State is read **before** two app Test control > Full power test activations (operator clarification). Apparent 0%/100% cycling and return to requested output require timed verification. No physical power-cycle evidence; narrowed retest below. |
| `s0-empty-custom-repeat-setup` | 136116/136117: query bank 06 / write selector 06; 136125: `03 F0 06 00` | Selecting reported custom Cycle 5 correlates with `06`; setup changes selector, not only reads. |
| `S0-empty-custom-repeat` | 136869: state selector 06; 136871 query; 136879 at 17:08:43.478: `03 F0 06 00` | Repeated independent empty-bank read, no custom write. |
| Missing `S0-empty-cycle-repeat` | C1-repeat snapshot inherits 137428–137486 at 17:13:03–17:13:53: selector 06→00→06, two bank-06 empty replies | Likely matching operator sequence; 17:17 denotes later report request, but its source file is absent. No bank-00 schedule reply or intermediate state read; add a timestamped controlled retest. |
| `C1-cycle-1-isolated-repeat` | 138105 at 17:21:48.949 writes selector 00; next C2 file 138541 at 17:26:59.468 reads 00 | Same-DUT repeat confirms Cycle 1 using later independent readback. Own report stops before the readback. |
| `C2-cycle-2-isolated-repeat` | 138602/138724 write selector 01; next I0 file 139212 at 17:31:01.853 reads 01 | Same-DUT repeat confirms Cycle 2. Unknown state-response tail is preserved, not interpreted as clock. |

The earlier historical `01`/`02` mapping remains a separate observation with
insufficient source/device metadata here. The current same-DUT repeats support
`00`/`01`; they do not resolve cross-firmware differences. Cycle 3 and an
unspecified Auto option are operator-reported unavailable, with no mapping
claim. Custom bank 06 being empty does not imply other custom banks are empty.

## Second batch: custom storage, selection and counts

| Case | Sent values / independent readback | Result and deviation |
| --- | --- | --- |
| I0 | 139270 at 17:31:21.885: `03 F1 05 02 91 1F 15 91 24 00`; I1 139708 at 17:35:57.135 reads same records | Reported Custom Cycle 4 = bank/selector `05`; points 17:31/21%, 17:36/0%. Own log has only the writes; next log confirms them. App sends default 100% on addition before the final desired levels. |
| I1 Cycle 1 | 139708 reads bank 05; 139826 at 17:36:01.899 writes selector `00`; reset 140114 reads `00` | Operator reports immediate 0→100% output. Selection happens just after the off point; there is no controlled observation across both future points. |
| I1 reset | 140209 queries `05`, 140210 selects `05`, 140220 reads unchanged `91 1F 15 / 91 24 00` | Return to custom storage without rewriting points; operator reports 100→0%. This is a mode reselection, not a power reset. |
| I2 Cycle 2 | 140966 reads unchanged bank 05; 140971 selects `01`; I4 144985 reads `01` | Stored points retained, but no Cycle 2 physical result is recorded. |
| I4 custom | 144999 queries `05`, 145000 selects `05`, 145008 reads same two points | Custom contents survive selecting both built-in cycles. Both original times have passed; no new scheduled physical transition is captured. |
| N0 | 145612 count `01`, 145617 at 17:49:21.787 count `00`; N1 145912 reads `03 F0 05 00` | Zero-count write/readback confirmed. Operator reports deletion returns output to the retained 81% Manual value when empty; this fallback needs a controlled physical repeat. |
| N1 | 146127 at 17:52:39.546: `03 F1 05 01 88 00 32`; N2 146524 reads same record | One record: 08:00/50%. Addition first transmits 100%, then 50%. |
| N2 | 146824 at 17:55:35.708: `03 F1 05 02 88 00 32 92 00 32`; N3 147161 reads both | Two records: 08:00/50%, 18:00/50%. Source filename says N1-two-record; mapped to N2 case. |
| N3 | 147362 at **17:58:38.448**: `03 F1 05 03 88 00 32 92 00 32 96 08 00`; T0800 150020 at 18:44:12.266 reads all three | Adds 22:08/0%. Bugreport request initiated 18:41:08, after the earlier action. Intermediate third-point levels 100% and 9% are also sent. |

Counts `00`–`03` are verified on the **same** custom bank by controlled edits
and independent later query responses. HCI LE connection-complete events
139569, 145788, 146391, 147027 and 149857 precede the relevant later sessions;
readback occurs before further schedule edits. This supports retention across
ordinary reconnects. It does not prove nonvolatile retention after power loss,
app-force-stop timing or the absence of an internal device commit operation.

The same selector occurs in `02 F1/F0` byte 4 and `03 0F/F0/F1` byte 2 for
these custom-bank interactions. Selecting a custom page issues both a query
and a state write; its schedule reply is not evidence of a passive query while
remaining in built-in mode. Built-in bank queries `00`/`01` lack corresponding
`03 F0` replies in these action intervals. No `03 F1` follows a built-in-cycle
selection until a custom point is edited. Schedule storage retention is
confirmed; physical scheduling precedence needs the inserted I-series retests.

The state brightness byte stays `51` (81 decimal) through operator-reported
0%, 21% and 100% automatic output. It is a retained Manual setpoint in this
session, not reliable measured automatic output. Full automatic output cannot
be inferred from that byte. The empty-bank fallback observation is recorded
as operator evidence and is not a safe-off guarantee.

## Third batch: time encoding and ordering

Each edited time has a corresponding transmitted three-byte point and an
independent lamp readback. On this DUT the first byte is `0x80 + hour`, the
second is binary minute, and the third is the level. This predicts all nine
sampled values including midnight and 23:59. The high bit is always set;
whether it is an enable flag is **unproven**. No BCD, minute reversal, or
minutes-since-midnight hypothesis is needed for these records.

| UI time | Edited record | Write frame / time BST | Readback frame / time BST | Record position |
| --- | --- | --- | --- | ---: |
| 08:00 | `88 00 32` | 150286 / 18:44:29.736 | 150853 / 18:47:26.518 (next file) | 2 |
| 08:01 | `88 01 32` | 151085 / 18:47:38.418 | 151431 / 18:47:48.715 | 2 |
| 08:30 | `88 1E 32` | 151908 / 18:50:38.651 | 152524 / 18:51:17.219 | 2 |
| 09:00 | `89 00 32` | 152680 / 18:53:41.108 | 153342 / 18:54:00.486 | 2 |
| 10:00 | `8A 00 32` | 153472 / 18:56:52.438 | 154105 / 18:57:15.572 | 2 |
| 12:00 | `8C 00 32` | 154259 / 19:00:02.498 | 154850 / 19:00:27.268 | 2 |
| 22:08 | `96 08 32` | 155015 / 19:03:13.689 | 155340 / 19:03:25.013 | 2 |
| 23:59 | `97 3B 32` | 155688 / 19:06:16.784 | 156023 / 19:06:46.255 | 3 |
| 00:00 | `80 00 32` | 156461 / 19:10:14.402 | 156791 / 19:10:26.996 | 1 |

The operator did **not** reduce the bank to one point as planned. The series
retains three points: fixed 08:00/50% and 22:08/0%, plus the edited 50% point.
At T0800 two exact 08:00/50% duplicates are transmitted and retained; T2208
retains two 22:08 points with different levels. This demonstrates stored
duplicates through the normal app path, not duplicate-time output precedence.
An additional controlled single-point/flag retest is inserted after T0800.

At T2359 and T0000 the app reorders the edited record in the **outgoing**
`03 F1` payload, matching the operator's UI notes. Readback has the same order.
Thus sorting already occurs before the lamp receives it; these logs cannot
test whether the lamp also sorts an unsorted payload. Track the edited point
by its time/level tuple rather than a fixed position after an order change.
The historical `22:08 -> 96 09` note is not reproduced: both N3 and T2208
encode minute 8 as `08`. Preserve the historical discrepancy as an attribution
uncertainty; under the new sampled formula `96 09` would denote 22:09.

## Fourth batch: brightness and incidental protocol traffic

| Case | Evidence | Result |
| --- | --- | --- |
| B0 | 157162 at 19:13:07.486 sets 12:34/50%; 157168 at 19:13:10.442 changes only level to `00`; 157781 at 19:13:26.399 reads `8C 22 00` | Final 0% write/readback confirmed. Setting up the new time in this case is a deviation; compare the final two writes. Three points remain. |
| B1 | 157948–158011 at 19:16:02.601–19:16:24.921; 158587 at 19:16:38.960 reads `8C 22 01` | Final 1% write/readback confirmed after 14 slider writes. Operator saw no discernible illumination; this does not establish a minimum physical level. |
| B10 (no supplied file) | Operator note says 9% was achieved, with visible output | No attributable packet or timestamp. B1's interim `09` writes are not evidence of this later B10 action. An exact-value retest is inserted directly below B10. |

B1's transmitted slider levels are **5, 4, 9, 0, 5, 12, 7, 9, 11, 8, 6,
8, 7, 1**. The app emits actual commands during adjustment; these are not
unsent drafts. Only the final 1% UI value is independently associated and
read back in this case. Together with I0's 21% (`15`) and N1/time-series 50%
(`32`), the controlled evidence supports direct percent encoding at 0, 1,
21 and 50. Default 100% (`64`) appears when adding points; a controlled B100
case is still not supplied. The earlier 50%/`2E` discrepancy is not reproduced.

In this series, schedule writes have **152-byte ATT values**, ending in bytes
148–151 `0F xx 00 30`; notifications have **150-byte values**, ending with
byte 149 `30`. Bytes between the declared records and the trailer are zero
in these snapshots. Brightness edits correlate `xx` with record index 0/1/2,
but time edits keep `xx=00` even when editing/reordering another record.
This is an observation, not a decoded universal index or checksum. A focused
trailer retest is inserted below B1. Padding does not prove maximum point
capacity; count-limit tests remain open.

An exhaustive pass over **all** DUT ATT packets in the latest cumulative log
finds additional family-04 writes in the reset-labeled case:

| Frame | Time BST | Full ATT value |
| --- | --- | --- |
| 135382 | 17:01:50.755 | `04 F0 00 00 00 00 00 00 00 00 00 00 00 00 00 40` |
| 135384 | 17:01:50.844 | `04 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 40` |
| 135388 | 17:01:54.565 | `04 F0 00 00 00 00 00 00 00 00 00 00 00 00 00 40` |
| 135390 | 17:01:54.999 | `04 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 40` |

These four writes are on the same HCI session and follow the state readback.
There is no observed family-04 notification or post-action state query in that
case. The next setup session reads unchanged `01/51/01` fields at 135989
(17:05:07.950), before selecting a different bank. This does not identify the
Full power test action's other effects. On 11 October the operator confirmed
that this was the app **Test control > Full power test** button, activated
twice. Output appears to cycle between 0% and 100% before returning to the
requested level; this is tentative operator evidence. The two family-04 pairs
are associated with those activations, but individual command roles, timing,
physical endpoints and restoration are unverified. The retest is narrowed to
one button press with timed output observations and before/after state and
bank reads. It no longer asks to identify the UI action or mix in an unplug/
replug test; physical power loss remains separately covered by P4. Original
case IDs and filenames are preserved.

The exhaustive ATT pass finds all DUT value-bearing application command
families `01`, `02`, `03`, `04`, `05`; GATT service-discovery values are not
treated as application messages. Writes are `0x52`, so there is no ATT Write
Response expected for them. No immediate application acknowledgment of any
of the 38 custom writes is observed; later query notifications establish
readback, not a direct write acknowledgment. Example MTU exchange at
157626/157634 is client 247/server 517, sufficient for these full values.
This refines the old description of universally 16-byte protocol frames.

All **79** captured DUT clock uploads encode little-endian year 2026, weekday
byte `06`, month/day `0A/0A`, and a time within one second of the packet's
Europe/London wall time. For example, 158566 at 19:16:38.674 BST sends
`01 0F EA 07 06 0A 0A 13 10 26 00 00 00 00 00 10`. The encoded 19:16:38
differs by +1 hour from UTC at that instant. This is consistent with local
BST time; the phone's configured timezone was confirmed retrospectively.
Operator confirmed on 11 October 2026 that the phone timezone was BST (UTC+01:00) throughout all prior tests. The captured clock uploads therefore match confirmed phone-local BST time, rather than UTC. A controlled timezone-shift test is still needed to establish behavior when the phone timezone changes.
No timezone change trial exists. Saturday `06` is observed, but the weekday convention
needs another weekday. Uploads occur after initialization and sometimes
again during a connection; they do not prove lamp clock accuracy or retention.

## Review completion and remaining tests

All 30 original files have an inventory record and a reviewed case/context
row. One named S0 case file is absent; related inherited packets were examined
and a retest is recorded. Unavailable UI options remain operator reports.
Planned cases without their own logs were initially marked “No supplied capture”.
The coverage follow-up below identifies which questions existing evidence resolves;
reused packet dates are explicitly distinguished from new test execution. Inserted retests immediately follow
their parent case and give concrete steps for the unresolved question.

Confirmed protocol observations are distinct from outstanding physical output,
power-loss persistence, commit timing, lamp firmware differences, timezone
shift, weekday mapping, high-bit/trailer meaning, and count-limit tests. None
of this app-driven discovery substitutes for ESPHome Gate A/T23/T15 acceptance.


### Documentation audit

After analysis, all 30 filenames are represented by reviewed case/context rows.
All 363 unique DUT application ATT values in the exhaustive latest-capture
extraction match the evidence CSV byte-for-byte, with matching frame number,
opcode, handle, timestamp and value length. Original log SHA256 hashes are
unchanged. All nine inserted retests sit directly below their parent case;
each contains executable app-driven steps and no invented capture date.
CSV parsing, unique case IDs and documentation whitespace checks pass. Workflow
checks were not monitored for this analysis task.

## Follow-up: retire redundant planned runs

On 11 October, the unexecuted case objectives were compared with the existing
packet inventory. **11 cases** are marked `Unnecessary — covered by existing
evidence`: B50, P1, P2, T1800, ORDER, both DUP cases, CLOCK normal reconnect,
LIFE reconnect, and PROTO write-ack/query-counts. Their CSV results identify
exact source frames, scope and deviations; original planned actions are retained.
No new capture or execution is claimed. In particular ORDER closes app-side
ordering, not whether the lamp would sort an unsorted write, and PROTO counts
closes observed counts 0–3, not a capacity limit.

Two conditional cases (B50 app-restart repeat and brightness-threshold follow-up)
are unnecessary for current findings because their discrepancy trigger is absent.
They must be reactivated if remaining exact-value trials expose a transition.
B100 remains open: default 100% traffic does not replace a controlled endpoint
trial. Missing exact values, force-stop/power-loss persistence, second-DUT trials,
manual levels, controlled mode changes, fresh-app/restart lifecycle, recorded
phone-zone baseline/zone shift and physical scheduling remain open. None of the
nine targeted retests is retired.

## 11 October bank retest: fresh capture and requested sequence

Source: `/srv/dev/data_projects/luminEze_bt_logs/protocol-test-S0-empty-cycle-repeat-RETEST-BANK-2026-10-11-113832.log`.
SHA256: `68e9e4d55123c5dd0f59232482bb3d77f22d2d63fc3a7558024ab08fc4df9f0e`.
The binary contains 2,678 frames from **11:35:27.771210 to 11:40:40.223792 BST
on 11 October**, with report request initiation **11:38:32 BST**. It has no
8–10 October history: this is a fresh session capture, unlike the original
30 cumulative snapshots. Background traffic from other devices remains.

The [separate retest evidence CSV](lumineze_ble_protocol_bank_retest_evidence.csv)
preserves 27 full DUT application values, using this file's local frame numbers.
The original 363-packet evidence set remains unchanged.

| Event | Frame(s) | Time BST | Evidence |
| --- | --- | --- | --- |
| Initial app session | 1483–1507 | 11:36:43–44 | Initialization, clock upload, state selector 05; bank 05 contains 08:00/50%, 12:34/9%, 22:08/0% |
| Select empty Cycle 5 | 2062/2063/2071 | 11:37:15.404–.527 | Query 06, write selector 06, reply `03 F0 06 00` |
| Select Cycle 1 | 2186 | 11:37:25.969 | `02 F1 01 51 00`; no later selector-00 read before return |
| Return to Cycle 5 | 2194/2195/2203 | 11:37:43.572–.656 | Query/write 06; empty bank reply in reassembled ACL |
| Close/reopen (operator); transport reconnect | 2206/2324 | 11:37:48.626 / 11:37:51.740 | Disconnect and new connection to same DUT; handle 0202 reused |
| Reopened state check | 2430/2434/2435 | 11:37:52.726–.817 | Query, independent `02 F0 01 51 06`, then app echo of 06 |
| Reopened empty bank check | 2436/2448 | 11:37:52.819–.962 | Query 06, independent `03 F0 06 00` |

No schedule write (`03 F1`) occurs. The requested sequence and Cycle 5
retention after reconnect are confirmed. Closing/reopening the app is operator
metadata; HCI directly establishes disconnect/reconnect and initialization.
The original retest's additional passive bank-comparison goal remains open:
no built-in bank-00 query/reply or intermediate selector-00 read occurs, and
selecting the custom page also writes selector 06. A narrowed follow-up row
tracks that remaining question.

Frame 2203's default tshark fields contain repeated ATT decode fields and
omit the first three application bytes. Inspecting its complete reassembled
157-byte ACL payload (`99 00 04 00 1B 0E 00 03 F0 06 00 ... 30`) confirms
a 150-byte notification value beginning `03 F0 06 00`; the evidence CSV
records that full value. Sunday's clock uploads use weekday `00` versus
Saturday's `06`, both with confirmed BST wall time. This supports the sampled
Saturday/Sunday convention; a complete weekday mapping remains unverified.

## 11 October I1 output retest

Source: `/srv/dev/data_projects/luminEze_bt_logs/protocol-test-I1-cycle-1-with-custom-RETEST-OUTPUT-2026-10-11-115212.log`.
SHA256: `b0e8319c3e306458474b8dab06d5885040fb795af0594bd0fe4f9163bfd80890`.
This 14,300-frame capture spans **11:35:27.771210–11:54:19.431207 BST**.
Its first 124,769 bytes hash to the preceding S0 retest's recorded SHA256,
confirming an exact cumulative prefix. Only appended frames **2679–14300**
are new evidence. The filename records report request initiation **11:52:12**.
The [I1 retest evidence CSV](lumineze_ble_protocol_i1_retest_evidence.csv)
preserves 42 new DUT values; inherited S0 values are not duplicated.

| Event | Frame(s) | Time BST | Evidence |
| --- | --- | --- | --- |
| Setup visits custom banks | 8331/8356/8368/8380 | 11:47:54–11:48:03 | Selectors 05/04/03/05; banks 04 and 03 reply count 0 |
| Setup edits then deletes 08:00 point | 8439/8452 | 11:48:10.615 / 11:48:15.285 | First writes 08:00/85%; then count 2 containing `8C 22 09 / 96 08 00` |
| Verify Cycle 4 / two points | 10576/10586 | 11:49:06.399 / .501 | State selector 05; bank 05 independently reads 12:34/9%, 22:08/0% |
| Select Cycle 1 | 10757 | 11:49:45.290 | `02 F1 01 51 00`; operator reports light turns to 100% |
| Return to Cycle 4 | 10762/10763 | 11:50:01.432 / .436 | Query bank 05 and write selector 05; operator reports reduced light |
| Verify retained contents | 10771 | 11:50:01.539 | Reassembled `03 F0 05 02 8C 22 09 96 08 00`; no schedule rewrite between selections |

The observations support an immediate physical effect of mode selection and
retention of custom storage. Reported 100% and subsequent reduction are
operator evidence, not brightness measurements from BLE. The reduced value
is unspecified. State byte `51` remains unchanged and cannot represent those
automatic outputs. No independent selector-00 readback occurs.

Both custom points are still in the future, but the controller remains in
Cycle 1 for only about 16 seconds and returns to Cycle 4 before either point.
The capture alone does not establish behavior across custom point times
while Cycle 1 stays selected. Subsequent operator confirmation resolves the
active-cycle precedence question, and the narrowed follow-up is now closed
(see clarification below). It also avoids inferring step/interpolation behavior
from the immediate reduction before the first point.

Frame 10771's reassembled ACL is `99 00 04 00 1B 0E 00 03 F0 05 02
8C 22 09 96 08 00 ... 30`; default tshark fields omit its first three value
bytes through repeated ATT decoding. Full 150-byte value is recovered from
the reassembled payload in the evidence CSV.

### Active-cycle precedence clarification

The operator confirmed on 11 October: **the cycle shown as selected in the
app is the cycle used by the lamp to adjust brightness**. This answers the
I1 question: selecting Cycle 1 makes it govern output while the bespoke bank
remains stored; selecting Cycle 4 makes that custom cycle govern output.
The I1 future-transition precedence follow-up is marked unnecessary, based
on this operator confirmation. The I1 packet evidence independently shows
selection writes and unchanged custom-bank readback; it does not supply a
timed physical trace across future points. No such trace is claimed.

This establishes the operating model by operator evidence; detailed custom
transition timing/interpolation, duplicate-time behavior and empty-bank
fallback remain separate questions. Other cases retain any distinct
requirements for exact selector readback or physical observations, rather
than repeating the now-resolved general precedence question.

## Stepped transitions and Manual/Auto investigation

On 11 October the operator confirmed that scheduled changes such as
**100% -> 50% -> 0% are sharp steps, with no gradual fading**. This resolves
I4's step-versus-interpolation question by physical observation. Its retest
is marked unnecessary; original timing-trace steps remain available if precise
latency is later needed. No new timed capture is claimed.

The operator also confirmed that the app has **no per-point enable/disable
control**. Selecting a schedule makes that schedule current. N1 already covers
the one-point 08:00/50% baseline, so the combined T0800 baseline/point-toggle
retest is retired. This UI clarification does not decode record bit `0x80`.

A new `MODE-manual-auto-schedule-bit` case investigates whether that bit
changes with global Manual/Auto mode. Hold the same custom bank, times,
levels and count fixed; capture Auto -> Manual -> Auto state writes,
independent state reads and any schedule traffic. Compare state mode, bank
selector, count, record hour bytes and trailer as separate fields. This
complements the existing Manual-to-Auto-Cycle-1 state test without changing
mode and bank together.

Schedule reads are valid Manual comparisons only if the app permits them
without switching back to Auto: capture state before and after the query.
Existing app custom-page access sends a state write, so an unchanged `0x80`
after that intervention cannot prove that the bit is unchanged in Manual.
If the app cannot expose a passive Manual read, record that limitation. A
repeatable change isolated to mode would support mode dependence; an
unchanged bit across verified modes would argue against a mode-enable
interpretation on this DUT. Neither result alone proves universal semantics.

## 11 October Auto/Manual comparison

Source: `/home/simon/dev/data_projects/luminEze_bt_logs/protocol-test-cycle_auto_manual_auto-2026-10-11-122033.log`.
SHA256: `0647505eb5c2c512c735c0fece50f10cfd567a4672a4ebae657c0d47f9e3447c`.
Fresh 2,415-frame capture: **12:18:45.403106–12:19:47.212969 BST**.
Report request initiation is **12:20:33 BST**, after the final packet.
This file does not contain the earlier session history.
The [mode evidence CSV](lumineze_ble_protocol_mode_evidence.csv) preserves
all 15 DUT application values, with file-local frame numbers.

Initial connection at frame 1507 (12:19:00.945) is followed by initialization,
clock upload and state query. Independent reply **1639 at 12:19:02.067**
is `02 F0 01 51 05 ...`: Auto, retained 81% Manual setpoint and bank 05.
Only afterward does app echo 1640 write `02 F1 01 51 05 ...`. Schedule
reply 1649 reads `03 F0 05 02 8C 22 09 96 08 00 ...`, the unchanged
12:34/9% and 22:08/0% records.

| Operator-associated mode | Frame | BST | Write prefix |
| --- | --- | --- | --- |
| Manual | 2032 | 12:19:11.785 | `02 F1 00 51 05` |
| Auto | 2035 | 12:19:15.842 | `02 F1 01 51 05` |
| Manual | 2097 | 12:19:21.924 | `02 F1 00 51 05` |
| Auto | 2151 | 12:19:23.816 | `02 F1 01 51 05` |

Full 16-byte writes differ only at **byte 2 (zero-based)**, associating
`00` with Manual and `01` with Auto while level, bank and trailer remain
fixed. No `03 F1` schedule write occurs. There is no independent state
read after the toggles and **no bank read while Manual is active**. Thus
this experiment isolates the global mode control but does not compare
schedule record bit `0x80` between modes. The bit remains unknown.

Operator confirms that opening the app and connecting retains the previous
Auto/Manual state unless explicitly changed. Initial Auto read-before-echo
supports that behavior on this connection. Retention of Manual on reopening
is operator-confirmed, not demonstrated by a Manual reconnect in this file.
An echo of the read mode must not be classified as an automatic reset.
This observation is distinct from changing the selected cycle/custom page,
which can issue an explicit state write.

The remaining Manual-bank follow-up first checks whether a passive read is
possible in the official app. If not, mark the app-driven bit comparison
unavailable rather than demand more mode-toggle captures. No correlation
with the hour high bit can be inferred from an Auto-only schedule response.
