"""Execute the production safe-off action lambdas with fake fixture storage."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LINES = (ROOT / "packages/topology/safe-off.yaml").read_text().splitlines()


def body(script_id):
    start = next(i for i, line in enumerate(LINES) if line.strip() == f"- id: {script_id}")
    start = next(i for i in range(start, len(LINES)) if LINES[i].strip() == "- lambda: |-")
    indent = len(LINES[start]) - len(LINES[start].lstrip())
    result = []
    for line in LINES[start + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        result.append(line[indent + 4 :])
    return "\n".join(result)


source = r"""
#include <cassert>
#include "components/lumineze_topology/transport_logic.h"
namespace lumineze_topology {
struct Binding { const char *id; int slot; int group; };
constexpr int group_count = 2;
constexpr Binding fixtures[] = {{"a", 0, 0}, {"b", 3, 0}, {"c", 1, 1}};
int group_off_count[2] = {};
int fixture_off_count[4] = {};
void group_controls_off(int group) { group_off_count[group]++; }
void fixture_control_off(int slot) { fixture_off_count[slot]++; }
void status(int, const char *) {}
}
struct State {
  lumineze_topology::GroupState topology_groups[4];
  lumineze_topology::FixtureState topology_fixtures[4];
} state;
#define id(name) state.name
void off_group(int group_index) {
__GROUP__
}
void off_all() {
__ALL__
}
int main() {
  for (int group = 0; group < 2; ++group) {
    state.topology_groups[group].automatic = true;
    state.topology_groups[group].manual = true;
  }
  for (int slot : {0, 1, 3}) {
    auto &fixture = state.topology_fixtures[slot];
    fixture.manual = true;
    fixture.target = 70;
  }
  off_group(0);
  assert(!state.topology_groups[0].automatic && !state.topology_groups[0].manual);
  assert(state.topology_groups[1].automatic && state.topology_groups[1].manual);
  for (int slot : {0, 3}) {
    const auto &fixture = state.topology_fixtures[slot];
    assert(!fixture.manual && fixture.target == 0 && fixture.pending);
    assert(fixture.source == lumineze_topology::SAFETY);
    assert(lumineze_topology::fixture_off_count[slot] == 1);
  }
  assert(state.topology_fixtures[1].target == 70);
  assert(lumineze_topology::fixture_off_count[1] == 0);

  auto &overridden = state.topology_fixtures[0];
  overridden.manual = true;
  overridden.manual_level = 35;
  assert(overridden.target == 0);
  const auto manual_source = lumineze_topology::resolve_source(
      false, overridden.manual, state.topology_groups[0].source);
  const auto manual = lumineze_topology::convert_fixture({
      manual_source, 100.0f, 0.0f, 0.0f, 0.0f, overridden.manual_level,
      overridden.target, 2, false, false, false, false,
      overridden.source != manual_source});
  assert(manual.valid && manual.submit && manual.target == 35);
  lumineze_topology::accept_target(
      overridden, manual.target, manual_source,
      state.topology_groups[0].revision, false);
  assert(overridden.target == 35 &&
         overridden.source == lumineze_topology::FIXTURE_MANUAL);

  const auto safety_source = lumineze_topology::resolve_source(
      true, overridden.manual, state.topology_groups[0].source);
  const auto safety = lumineze_topology::convert_fixture({
      safety_source, 100.0f, 0.0f, 0.0f, 0.0f, 0, overridden.target, 2,
      false, false, false, false, overridden.source != safety_source});
  assert(safety.valid && safety.target == 0);
  off_all();
  for (int group = 0; group < 2; ++group)
    assert(!state.topology_groups[group].automatic &&
           !state.topology_groups[group].manual);
  for (int slot : {0, 1, 3}) {
    const auto &fixture = state.topology_fixtures[slot];
    assert(!fixture.manual && fixture.target == 0 && fixture.pending);
    assert(fixture.source == lumineze_topology::SAFETY);
  }
}
"""

with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / "safe_off.cpp"
    executable = Path(directory) / "safe_off"
    cpp.write_text(source.replace("__GROUP__", body("topology_safe_off_group"))
                        .replace("__ALL__", body("topology_safe_off_all")))
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT),
         str(cpp), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
print("Production group/controller safe-off scopes passed")
