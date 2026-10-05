"""Validate real generic ESPHome packages across bounded fixture topologies.

This is a CI-only fixture writer. Device Builder installations use ordinary
package includes; they never run this script.

Usage: python3 scripts/check_topology_matrix.py [--compile] uvx --python 3.14
       --from esphome==2026.9.0 esphome
"""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / "ci"


def compose(name, contexts, groups, fixtures, *, experimental=False, reserved=(),
            development=False, engine="seasonal"):
    controller_package = (
        "../packages/lumineze-topology-development.yaml"
        if development else "../packages/lumineze-topology.yaml"
    )
    if engine == "schedule":
        controller_package = "../packages/schedule-" + ("development" if development else "production") + ".yaml"
    lines = [
        f"# Generated CI fixture: {name}",
        "substitutions:",
        f"  device_name: {'s-' + name.removeprefix('schedule-') if engine == 'schedule' else 'topology-' + name}",
        f"  ble_connection_slots: '{max(2, len(fixtures))}'",
        "packages:",
        f"  controller: !include {controller_package}",
    ]
    for context in contexts:
        lines.extend(
            [
                f"  context_{context}: !include",
                f"    file: ../packages/topology/context-{engine}.yaml",
                f"    vars: {{context_id: {context}, context_name: {context}}}",
            ]
        )
    if engine == "schedule":
        for context in contexts:
            roles = sorted({role for _, owner, role in groups if owner == context})
            for role in roles:
                lines.extend([f"  editor_{context}_{role}: !include",
                    "    file: ../packages/topology/context-schedule-role.yaml",
                    f"    vars: {{context_id: {context}, schedule_role: {role}}}"])
    for group, _, _ in groups:
        lines.extend(
            [
                f"  group_{group}: !include",
                "    file: ../packages/topology/group.yaml",
                f"    vars: {{group_id: {group}, group_name: {group}}}",
            ]
        )
    for identity, _slot, product, _group, mac in fixtures:
        maximum = 100 if product == "jungle_dawn" else 0
        lines.extend(
            [
                f"  fixture_{identity}: !include",
                "    file: ../packages/topology/fixture-luminize.yaml",
                "    vars:",
                f"      fixture_id: {identity}",
                f"      fixture_name: {identity}",
                f"      fixture_mac: '{mac}'",
                f"      fixture_default_maximum: {maximum}",
            ]
        )
    lines.extend(
        [
            "external_components:",
            "  - source: {type: local, path: ../components}",
            "    components: [lumineze_topology]",
            "lumineze_topology:",
            "  topology_version: 1",
            f"  engine_family: {engine}",
            f"  input_provider: {'development' if development else 'real'}",
            f"  allow_experimental_topology: {'true' if experimental else 'false'}",
            "  contexts:",
        ]
    )
    for context in contexts:
        lines.append(f"    - {{id: {context}}}")
    lines.append("  groups:")
    for group, context, role in groups:
        lines.append(f"    - {{id: {group}, context: {context}, output: {role}}}")
    lines.append("  fixtures:")
    for identity, slot, product, group, mac in fixtures:
        lines.append(
            f"    - {{id: {identity}, slot: {slot}, type: {product}, "
            f"group: {group}, mac: '{mac}'}}"
        )
    for identity, slot in reserved:
        lines.append(f"    - {{id: {identity}, slot: {slot}, enabled: false}}")
    lines.extend(["wifi:", "  ssid: ci-network", "  password: ci-password"])
    return "\n".join(lines) + "\n"


MACS = [f"AA:BB:CC:DD:EE:{index:02X}" for index in range(1, 5)]
CASES = [
    (
        "visible-sparse",
        ["shared"],
        [("visible", "shared", "visible")],
        [("jungle", 3, "jungle_dawn", "visible", MACS[0])],
        False,
        [("reserved_uv", 0)],
    ),
    (
        "uv-zero",
        ["shared"],
        [("uv", "shared", "uv")],
        [("uv_lamp", 0, "prot5", "uv", MACS[0])],
        False,
        [],
    ),
    (
        "visible-shared",
        ["shared"],
        [("visible", "shared", "visible")],
        [("jungle_a", 0, "jungle_dawn", "visible", MACS[0]),
         ("jungle_b", 1, "jungle_dawn", "visible", MACS[1])],
        False,
        [],
    ),
    (
        "visible-reordered",
        ["shared"],
        [("visible", "shared", "visible")],
        [("jungle_b", 1, "jungle_dawn", "visible", MACS[1]),
         ("jungle_a", 0, "jungle_dawn", "visible", MACS[0])],
        False,
        [],
    ),
    (
        "uv-shared",
        ["shared"],
        [("uv", "shared", "uv")],
        [("uv_a", 1, "prot5", "uv", MACS[0]),
         ("uv_b", 3, "prot5", "uv", MACS[1])],
        False,
        [],
    ),
    (
        "reversed-mixed",
        ["shared"],
        [("visible", "shared", "visible"), ("uv", "shared", "uv")],
        [("uv_lamp", 0, "prot5", "uv", MACS[0]),
         ("jungle", 1, "jungle_dawn", "visible", MACS[1])],
        False,
        [],
    ),
    (
        "independent-groups",
        ["shared"],
        [("visible_a", "shared", "visible"),
         ("visible_b", "shared", "visible")],
        [("jungle_a", 0, "jungle_dawn", "visible_a", MACS[0]),
         ("jungle_b", 1, "jungle_dawn", "visible_b", MACS[1])],
        False,
        [],
    ),
    (
        "four-shared",
        ["shared"],
        [("visible", "shared", "visible"), ("uv", "shared", "uv")],
        [("jungle_a", 0, "jungle_dawn", "visible", MACS[0]),
         ("uv_a", 1, "prot5", "uv", MACS[1]),
         ("jungle_b", 2, "jungle_dawn", "visible", MACS[2]),
         ("uv_b", 3, "prot5", "uv", MACS[3])],
        True,
        [],
    ),
    (
        "four-independent",
        ["viv_a", "viv_b"],
        [("a_visible", "viv_a", "visible"), ("a_uv", "viv_a", "uv"),
         ("b_visible", "viv_b", "visible"), ("b_uv", "viv_b", "uv")],
        [("jungle_a", 0, "jungle_dawn", "a_visible", MACS[0]),
         ("uv_a", 1, "prot5", "a_uv", MACS[1]),
         ("jungle_b", 2, "jungle_dawn", "b_visible", MACS[2]),
         ("uv_b", 3, "prot5", "b_uv", MACS[3])],
        True,
        [],
    ),
    (
        "development-input",
        ["shared"],
        [("visible", "shared", "visible")],
        [("jungle", 0, "jungle_dawn", "visible", MACS[0])],
        False,
        [],
        True,
    ),
]


def main():
    arguments = sys.argv[1:]
    engine = "schedule" if "--schedule" in arguments else "seasonal"
    if "--schedule" in arguments:
        arguments.remove("--schedule")
    compile_firmware = "--compile" in arguments
    if compile_firmware:
        arguments.remove("--compile")
    if not arguments:
        raise SystemExit("pass an ESPHome command")
    assignment_maps = {}
    for case in CASES:
        name, contexts, groups, fixtures, experimental, reserved = case[:6]
        development = case[6] if len(case) > 6 else False
        if engine == "schedule":
            name = "schedule-" + name
        source = compose(name, contexts, groups, fixtures,
                         experimental=experimental, reserved=reserved,
                         development=development, engine=engine)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", prefix="topology-matrix-", dir=CI
        ) as temporary:
            temporary.write(source)
            temporary.flush()
            for action in ("config", "compile") if compile_firmware else ("config",):
                result = subprocess.run(
                    [*arguments, action, temporary.name],
                    cwd=ROOT, capture_output=True, text=True, check=False
                )
                output = result.stdout + result.stderr
                if result.returncode:
                    raise AssertionError(
                        f"{name} {action} failed:\n{output[-2500:]}"
                    )
                if action == "config":
                    client_ids = set(re.findall(r"(?m)^  - id: (\w+)_client$", output))
                    expected = {fixture[0] for fixture in fixtures}
                    if client_ids != expected:
                        raise AssertionError(
                            f"{name}: clients {client_ids} differ from {expected}"
                        )
                if action == "compile" and name.endswith("visible-shared") or action == "compile" and name.endswith("visible-reordered"):
                    build_name = "s-" + name.removeprefix("schedule-") if engine == "schedule" else "topology-" + name
                    cpp = CI / ".esphome/build" / build_name / "src/main.cpp"
                    rows = re.findall(
                        r'\{"([a-z_]+)", (\d+), (\d+), (0x[0-9A-F]+)U\}',
                        cpp.read_text(),
                    )
                    assignment_maps[name.removeprefix("schedule-")] = {
                        identity: (int(slot), key) for identity, slot, _group, key in rows
                    }
                print(f"PASS {name} {action}")
    if compile_firmware:
        if assignment_maps["visible-shared"] != assignment_maps["visible-reordered"]:
            raise AssertionError("fixture reorder changed slot or calibration identity")
        print("PASS declaration reorder preserves slot and calibration identity")


if __name__ == "__main__":
    main()
