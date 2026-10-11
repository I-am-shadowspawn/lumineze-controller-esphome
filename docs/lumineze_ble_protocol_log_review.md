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
Filename times identify report labels, while packet times identify BLE actions.
Several captures continue about two minutes after their filename time.

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
| `full-power-reste` | 135375 at 17:01:46.418: `02 F0 01 51 01`; 135377 queries bank 01 without schedule reply | State after operator-reported resets matches prior selector. Only one app session is visible; power boundaries, custom persistence and clock retention are inconclusive. Clock upload precedes readback. Retest added. |
| `s0-empty-custom-repeat-setup` | 136116/136117: query bank 06 / write selector 06; 136125: `03 F0 06 00` | Selecting reported custom Cycle 5 correlates with `06`; setup changes selector, not only reads. |
| `S0-empty-custom-repeat` | 136869: state selector 06; 136871 query; 136879 at 17:08:43.478: `03 F0 06 00` | Repeated independent empty-bank read, no custom write. |
| Missing `S0-empty-cycle-repeat` | C1-repeat snapshot inherits 137428–137486 at 17:13:03–17:13:53: selector 06→00→06, two bank-06 empty replies | Likely matching operator sequence, but named 17:17 file absent. No bank-00 schedule reply or intermediate state read; add a timestamped controlled retest. |
| `C1-cycle-1-isolated-repeat` | 138105 at 17:21:48.949 writes selector 00; next C2 file 138541 at 17:26:59.468 reads 00 | Same-DUT repeat confirms Cycle 1 using later independent readback. Own report stops before the readback. |
| `C2-cycle-2-isolated-repeat` | 138602/138724 write selector 01; next I0 file 139212 at 17:31:01.853 reads 01 | Same-DUT repeat confirms Cycle 2. Unknown state-response tail is preserved, not interpreted as clock. |

The earlier historical `01`/`02` mapping remains a separate observation with
insufficient source/device metadata here. The current same-DUT repeats support
`00`/`01`; they do not resolve cross-firmware differences. Cycle 3 and an
unspecified Auto option are operator-reported unavailable, with no mapping
claim. Custom bank 06 being empty does not imply other custom banks are empty.
