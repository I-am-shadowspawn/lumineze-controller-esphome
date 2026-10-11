# LuminEZE BLE protocol findings

Updated 11 October 2026 after review of all 30 supplied HCI snoop logs against
[the test plan](lumineze_ble_protocol_test_plan.md) and
[case records](lumineze_ble_protocol_case_records.csv). These are observations
from the official app, not ESPHome hardware acceptance.

The operator identifies a Motorola Edge 40 / Android 15, app V1.1.4 and a
JungleDawn 39W; the lamp firmware version is unspecified. Peer-address filtering
separates that DUT from another lamp visited during early captures. All 30
files are exact cumulative prefixes, so copied history is counted once.
The operator confirmed that filename timestamps identify **bugreport request
initiation** in BST, not BLE action times or report completion. Packet times
determine the actual actions; capture end is the final recorded packet.

The [case-level log review](lumineze_ble_protocol_log_review.md) records frame
pairs, deviations and interpretation. The [packet evidence CSV](lumineze_ble_protocol_packet_evidence.csv)
preserves full ATT values with frame, timestamp, direction, handle/opcode and
length. The [capture inventory](lumineze_ble_protocol_capture_inventory.csv)
records original filenames, hashes and absolute packet bounds. The case CSV
marks analysis completion independently of test success, and places required
retests directly below the relevant case. [Historical findings](lumineze_ble_protocol_historical_findings.md)
preserve previous observations without presenting disputed claims as current facts.

## Transport and message shape

Commands are ATT Write Commands (`0x52`) on handle `0x0011`; device responses
are notifications (`0x1B`) on `0x000E`. Prior discovery identifies service FFF0
and command characteristic FFF2; handles are specific to the captured device.
An example MTU exchange is client 247 / server 517 (frames 157626/157634).
Operating, query, initialization and clock values are 16 bytes here. Custom
schedule writes are **152 bytes**, and schedule responses are **150 bytes**.
An implementation must not assume every command fits a 16-byte frame.

The 38 captured schedule writes receive no distinct immediate application
acknowledgment in this trace. ATT Write Command has no ATT Write Response.
Later independently issued schedule queries provide readback; they are not
write acknowledgments. A transmitted write alone does not prove retention or
physical lamp output.

## Initialization and clock upload

Initialization pairs are:

```text
App:  05 F0 00 01 02 03 04 00 00 00 00 00 00 00 00 50
Lamp: 05 F0 01 01 02 03 04 00 00 00 00 00 00 00 00 50
```

All 79 DUT clock uploads match the capture's Europe/London wall time within
one second. A representative frame 158566 at 19:16:38.674 BST is:

```text
01 0F EA 07 06 0A 0A 13 10 26 00 00 00 00 00 10
      year  wk mo dy hr mi se
```

`EA 07` is little-endian 2026, month/day are 10/10, hour/minute/second are
19/16/38, and weekday is `06` on this Saturday. This encoded hour is +1 from
UTC, consistent with BST/local wall time in this capture. The phone timezone
was confirmed retrospectively. Operator confirmed on 11 October 2026 that the phone timezone was BST (UTC+01:00) throughout all prior tests. The captured clock uploads therefore match confirmed phone-local BST time, rather than UTC. A controlled timezone-shift test is still needed to establish behavior when the phone timezone changes.
No controlled timezone change was captured; the general
timezone rule and weekday numbering require the planned follow-ups. Clock
uploads follow initialization and sometimes repeat later in a session. Upload
traffic does not prove lamp clock accuracy or survival through power loss.

## Operating state and cycle selection

Using zero-based full-command byte offsets:

| Field | Current observation | Confidence / limit |
| --- | --- | --- |
| Bytes 0–1 | `02 0F` query, `02 F0` response, `02 F1` write | Confirmed families |
| Byte 2 | `00` Manual, `01` Automatic | Supported by mode changes and prior capture context |
| Byte 3 | Retained Manual setpoint, direct percentage in observed states | **Not** measured automatic output: remains `51` while operator reports other levels |
| Byte 4 | Selected built-in cycle/custom bank | Same-DUT write and readback support |
| Remaining state-response bytes | Some resemble date/time; an irregular response also occurs | Preserve raw values; not fully decoded |

On this DUT/app, Cycle 1 maps to `00` and Cycle 2 to `01`. Write/readback pairs
are 127870/128749 and 129312/130088, repeated by 138105/138541 and
138602–138724/139212 across adjacent snapshots. An app echo after receiving
state is distinguished from the actual selector change. Custom Cycle 4 in the
operator notes uses `05`; Custom Cycle 5 uses `06`.

The historical Cycle 1=`01`, Cycle 2=`02` association belongs to a different
capture context and is not resolved as a universal firmware mapping. Cycle 3
and unspecified/default Auto are operator-reported unavailable here. Do not
substitute Cycle 1 for an unavailable default option.

## Schedule banks and record count

```text
03 0F <bank> ...                 query
03 F0 <bank> <count> <records>   response
03 F1 <bank> <count> <records>   write
```

Byte 2 varies with the bank/selector; the historical constant-`02` hypothesis
is disproven by queried banks `02`, `05` and `06`. Byte 3 is the record count.
Bank 06 is independently read empty, while bank 02 contains one record in the
earlier action window. “Empty custom schedule” is therefore a bank-specific
statement.

Counts 0–3 on bank 05 have controlled final writes and subsequent independent
readback before more edits:

| Count | Final write | Independent readback | Records |
| ---: | ---: | ---: | --- |
| 0 | 145617 | 145912 | Empty |
| 1 | 146127 | 146524 | 08:00/50% |
| 2 | 146824 | 147161 | 08:00/50%, 18:00/50% |
| 3 | 147362 | 150020 | 08:00/50%, 18:00/50%, 22:08/0% |

N3's write is at **17:58:38.448 BST**; its filename records bugreport request
initiation at **18:41:08 BST**. This is a delayed report, not a filename error.
Its later readback is at 18:44:12.266. New LE connections precede the subsequent
reads, supporting ordinary reconnect retention. Immediate commit timing,
force-stop persistence and power-loss persistence remain unresolved.

## Three-byte schedule point encoding

Records begin at byte 4 and have three-byte stride. Controlled writes and
matching notifications support this sampled mapping:

```text
record[0] = 0x80 + hour
record[1] = minute (binary)
record[2] = percentage (binary, for the controlled values below)
```

| UI time | Hour/minute bytes | Write / readback frames |
| --- | --- | --- |
| 08:00 | `88 00` | 150286 / 150853 |
| 08:01 | `88 01` | 151085 / 151431 |
| 08:30 | `88 1E` | 151908 / 152524 |
| 09:00 | `89 00` | 152680 / 153342 |
| 10:00 | `8A 00` | 153472 / 154105 |
| 12:00 | `8C 00` | 154259 / 154850 |
| 22:08 | `96 08` | 155015 / 155340 |
| 23:59 | `97 3B` | 155688 / 156023 |
| 00:00 | `80 00` | 156461 / 156791 |

The high bit is always set in these records. Its possible enable/flag meaning
has **not** been tested. The historical `22:08 -> 96 09` association is not
reproduced; the new series uses `96 08` and would decode `96 09` as 22:09.
Preserve the historical note as an attribution discrepancy.

The time series retains three points rather than the planned one-point setup.
T0800 transmits and reads two exact 08:00/50% duplicates; T2208 retains equal
times with different levels. The app reorders the outgoing records at T2359
and T0000, already before transmission. Lamp-side sorting and duplicate-time
physical precedence are not established.

## Brightness and live adjustment

| Controlled UI value | Record level byte | Evidence |
| ---: | --- | --- |
| 0% | `00` | B0 157168 / 157781 |
| 1% | `01` | B1 158011 / 158587 |
| 21% | `15` | I0 139270 / I1 139708 |
| 50% | `32` | N1 146127 / N2 146524 and time series |

Default newly added points also transmit `64` (100 decimal), supporting the
upper endpoint, but a controlled B100 test was not supplied. The earlier
50%/`2E` discrepancy is not reproduced; `2E` is 46 decimal, and there is no
basis to retain it as a general 50% encoding. Its original UI attribution
requires a controlled repeat rather than a guessed nonlinear formula.

B1 emits 14 real writes during adjustment, at levels 5,4,9,0,5,12,7,9,11,8,6,
8,7,1. Only the final 1% UI value is independently confirmed in that case.
The operator reports no discernible light at 1%; this is a visibility observation,
not evidence of a digital-level transformation or a minimum lamp output.
B10's operator note says 9% was achieved, but no capture is supplied; B1's
interim `09` packets cannot stand in for that later action.

## Trailers and limits

Observed writes end at offsets 148–151 with `0F xx 00 30`; 150-byte responses
end with byte 149=`30`. The region after declared records is zero in these
snapshots. Brightness changes correlate `xx` with the changed record index
0/1/2, while time changes keep `xx=00` even when another record is changed or
reordered. The trailer's purpose is unresolved. Neither the zero-filled region
nor total payload length establishes maximum count, checksum, or enable flags.
A separate trailer retest is recorded, and planned capacity tests remain open.

## Family 04: app Full power test

The same session sends two pairs:

```text
135382 / 17:01:50.755: 04 F0 00 00 00 00 00 00 00 00 00 00 00 00 00 40
135384 / 17:01:50.844: 04 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 40
135388 / 17:01:54.565: 04 F0 00 00 00 00 00 00 00 00 00 00 00 00 00 40
135390 / 17:01:54.999: 04 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 40
```

The operator clarified on 11 October that the original “full power reset”
case means **Test control > Full power test** in the app, pressed twice. The
two command pairs are associated with those activations, not physical power
cycling. The lamp appears to cycle between 0% and 100% before returning to
the requested level; this is a tentative operator observation, not a timed
confirmation of sequence, endpoints or restoration. Individual roles of
`04 F0` and `04 0F` remain unknown.

There is no family-04 response or same-report post-action state read. The
next setup reads unchanged `01/51/01` at 135989 before any selector change;
this alone does not confirm physical output restoration or schedule retention.
The retest now focuses on one button press, timed physical observations and
before/after state and bank reads. Physical power-loss persistence remains a
separate P4 test. Legacy case IDs and filenames are retained for traceability.

## Storage and physical behavior boundaries

I0's 17:31/21% and 17:36/0% custom points are independently read before and
after built-in cycle selections. Contents survive ordinary reconnects and
selector changes. Opening the custom page also writes its selector, so the
readback is not a passive query while remaining in built-in mode. Built-in
bank 00/01 queries have no matching schedule reply in the relevant intervals.

Operator-reported immediate output changes (custom 0% to Cycle 1 100%, then
back to 0%) suggest different active output modes, but do not prove precedence
through both scheduled transitions. Deleting all custom points was reported
to restore 81% Manual output. That fallback requires physical confirmation;
an empty custom bank cannot be treated as a guaranteed off state.

## Remaining work and confidence

Sampled time bytes, counts 0–3, final levels 0/1/21/50, same-DUT selectors and
custom-bank retention across normal reconnects have independent readback
support. Cross-firmware mapping, physical precedence, empty-bank fallback,
power-loss/force-stop persistence, commit timing, timezone change and weekday
convention, high-bit/trailer semantics and capacity limits remain open.

All supplied logs are reviewed; cases without supplied logs remain explicitly
unreviewed. The case CSV contains concrete retest steps immediately below each
inconclusive logged case and separate planned cases for broader coverage.
No malformed packets were sent, and no firmware implementation or runtime
hardware acceptance claim is introduced by this documentation review.

## 11 October fresh bank retest

A new capture (separate from the 30 cumulative snapshots) confirms selector
writes `06 -> 00 -> 06` for Cycle 5 -> Cycle 1 -> Cycle 5, then independent
selector-06 state readback before the app echo after disconnect/reconnect.
Bank 06 is empty before and after; no schedule write occurs. The intended
passive comparison while retaining built-in mode remains untested. See the
[bank retest review](lumineze_ble_protocol_log_review.md#11-october-bank-retest-fresh-capture-and-requested-sequence)
and [packet evidence](lumineze_ble_protocol_bank_retest_evidence.csv).
