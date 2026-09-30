"""Exercise the real ESPHome config validator against topology mutations.

Usage: python3 scripts/check_topology_schema.py uvx --python 3.14 --from
       esphome==2026.9.0 esphome
"""

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "ci/topology-proof/controller.yaml"
FOUR = ROOT / "ci/topology-proof/four.yaml"


def run_case(command, title, source, old=None, new=None, expected=None):
    if old is not None:
        count = source.count(old)
        if count != 1:
            raise AssertionError(f"{title}: mutation matches {count} times")
        source = source.replace(old, new)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix="topology-check-", dir=PROOF.parent
    ) as temporary:
        temporary.write(source)
        temporary.flush()
        result = subprocess.run(
            [*command, "config", temporary.name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    output = result.stdout + result.stderr
    if expected is None:
        if result.returncode:
            raise AssertionError(f"{title}: expected valid config; {output[-1500:]}")
    elif result.returncode == 0 or expected not in output:
        raise AssertionError(
            f"{title}: expected failure containing {expected!r}; {output[-1500:]}"
        )
    print(f"PASS {title}")


def main():
    command = sys.argv[1:]
    if not command:
        raise SystemExit("pass an ESPHome command, e.g. uvx ... esphome")
    two = PROOF.read_text()
    four = FOUR.read_text()
    run_case(command, "two repeated products and sparse slots", two)
    run_case(command, "four fixtures and two contexts", four)
    cases = [
        (
            "duplicate MAC",
            "\n      mac: AA:BB:CC:DD:EE:02",
            "\n      mac: AA:BB:CC:DD:EE:01",
            "duplicate enabled address",
        ),
        (
            "BLE binding mismatch",
            "fixture_mac: AA:BB:CC:DD:EE:02",
            "fixture_mac: AA:BB:CC:DD:EE:03",
            "binding address differs",
        ),
        (
            "role mismatch",
            "output: visible",
            "output: uv",
            "product role does not match",
        ),
        (
            "unknown group",
            "group: visible_group\n      mac: AA:BB:CC:DD:EE:02",
            "group: absent_group\n      mac: AA:BB:CC:DD:EE:02",
            "unknown group",
        ),
        (
            "duplicate slot",
            "slot: 3",
            "slot: 0",
            "duplicate slot",
        ),
        (
            "zero MAC",
            "\n      mac: AA:BB:CC:DD:EE:02",
            "\n      mac: 00:00:00:00:00:00",
            "placeholder or broadcast",
        ),
        (
            "missing transaction binding",
            "fixture_id: fixture_b",
            "fixture_id: other_fixture",
            "BLE client bindings must match",
        ),
    ]
    for title, old, new, error in cases:
        run_case(command, title, two, old, new, error)
    run_case(
        command,
        "four fixtures require experimental opt-in",
        four,
        "allow_experimental_topology: true",
        "allow_experimental_topology: false",
        "required for more than two fixtures",
    )


if __name__ == "__main__":
    main()
