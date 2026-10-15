"""Check generic adapter frames/delay order against both v1 product paths."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
legacy = (ROOT / "packages/lamps/protocol.yaml").read_text()
generic = (ROOT / "packages/topology/fixture-luminize-common.yaml").read_text()
generic_adapter = generic.split("\nscript:", 1)[1]


def static_frames(source):
    return [
        tuple(re.findall(r"0x[0-9A-Fa-f]{2}", match))
        for match in re.findall(r"value:\s*\[([^]]+)\]", source, re.S)
    ]


old = static_frames(legacy)
new = static_frames(generic)
assert len(old) == 4 and len(new) == 2, (len(old), len(new))
assert old[:2] == old[2:] == new
assert all(len(frame) == 16 for frame in new)

old_dynamic = [
    tuple(re.findall(r"0x[0-9A-Fa-f]{2}", match))
    for match in re.findall(r"return\s*\{(0x02,\s*0xF1,.*?)};", legacy, re.S)
]
new_dynamic = [
    tuple(re.findall(r"0x[0-9A-Fa-f]{2}", match))
    for match in re.findall(r"return\s*\{(0x02,\s*0xF1,.*?)};", generic, re.S)
]
assert len(old_dynamic) == 2 and len(new_dynamic) == 1
assert old_dynamic[0] == old_dynamic[1] == new_dynamic[0]

old_delays = re.findall(r"- delay:\s*(\S+)", legacy)
new_delays = re.findall(r"- delay:\s*(\S+)", generic)
assert old_delays[:3] == old_delays[3:] == new_delays == ["1s", "200ms", "300ms"]
assert legacy.count('service_uuid: "0000FFF0"') == 6
assert generic_adapter.count("service_uuid: '0000FFF0'") == 3
assert legacy.count('characteristic_uuid: "0000FFF2"') == 6
assert generic_adapter.count("characteristic_uuid: '0000FFF2'") == 3
print("Protocol frames, UUIDs and delay order match both v1 adapters")
