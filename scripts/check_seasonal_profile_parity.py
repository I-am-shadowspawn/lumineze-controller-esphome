"""Compare real and live-development snapshots used by seasonal profiles."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def lambda_body(path, anchor):
    lines = (ROOT / path).read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if anchor in line)
    start = next(i for i in range(start, len(lines))
                 if lines[i].strip() == "- lambda: |-")
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line[indent + 4:])
    return "\n".join(body)


source = r"""
#include <cassert>
#include <cmath>
#include "components/lumineze_topology/runtime_types.h"

struct ClockValue {
  bool valid = true;
  int year = 2026, day_of_year = 1, hour = 0, minute = 0, second = 0;
  bool is_valid() const { return valid; }
};
struct Clock {
  ClockValue value;
  ClockValue now() const { return value; }
};
struct Switch { bool state = false; };
struct Number { float state = 0.0f; };
struct State {
  Clock controller_time;
  bool evaluation_snapshot_valid = false;
  int evaluation_snapshot_year = 0;
  int evaluation_snapshot_day = 0;
  int evaluation_snapshot_days_in_year = 365;
  float evaluation_snapshot_minutes = 0.0f;
  bool evaluation_snapshot_simulated = false;
  bool evaluation_simulation_output_enabled = false;
  Switch solar_test_mode, solar_simulated_output_enable;
  Number solar_test_year{2024}, solar_test_calendar_day{60},
      solar_test_time_minutes{754.75f};
  lumineze_topology::EvaluationSnapshot topology_snapshot;
  Switch topology_simulation_enabled, topology_simulated_output_enable;
  Number topology_simulation_year{2024}, topology_simulation_day{60},
      topology_simulation_time{754.75f};
} state;
#define id(name) state.name

void legacy_real() {
__LEGACY_REAL__
}
void legacy_development() {
__LEGACY_DEVELOPMENT__
}
void topology_real() {
__TOPOLOGY_REAL__
}
void topology_development() {
__TOPOLOGY_DEVELOPMENT__
}

void assert_same_live_legacy_snapshot() {
  assert(state.evaluation_snapshot_valid);
  assert(!state.evaluation_snapshot_simulated);
  assert(!state.evaluation_simulation_output_enabled);
  assert(state.evaluation_snapshot_year == state.topology_snapshot.year);
  assert(state.evaluation_snapshot_day == state.topology_snapshot.day_of_year);
  assert(state.evaluation_snapshot_days_in_year ==
         state.topology_snapshot.days_in_year);
  assert(std::fabs(state.evaluation_snapshot_minutes -
                   state.topology_snapshot.minutes) < 0.0001f);
}

int main() {
  state.controller_time.value = {true, 2024, 60, 12, 34, 45};
  legacy_real();
  topology_real();
  assert_same_live_legacy_snapshot();

  state.solar_test_mode.state = true;
  state.solar_simulated_output_enable.state = true;
  state.topology_simulation_enabled.state = true;
  state.topology_simulated_output_enable.state = true;
  legacy_development();
  topology_development();
  assert(state.evaluation_snapshot_valid && state.evaluation_snapshot_simulated);
  assert(state.evaluation_simulation_output_enabled);
  assert(state.topology_snapshot.valid && state.topology_snapshot.simulated);
  assert(state.topology_snapshot.simulated_output_enabled);
  assert(state.evaluation_snapshot_year == state.topology_snapshot.year);
  assert(state.evaluation_snapshot_day == state.topology_snapshot.day_of_year);
  assert(state.evaluation_snapshot_days_in_year ==
         state.topology_snapshot.days_in_year);
  assert(std::fabs(state.evaluation_snapshot_minutes -
                   state.topology_snapshot.minutes) < 0.0001f);

  // Leaving simulation must clear a still-on bench switch in both providers.
  state.solar_test_mode.state = false;
  state.topology_simulation_enabled.state = false;
  legacy_development();
  topology_development();
  legacy_real();
  topology_real();
  assert_same_live_legacy_snapshot();

  state.controller_time.value.valid = false;
  legacy_real();
  topology_real();
  assert(!state.evaluation_snapshot_valid && !state.topology_snapshot.valid);
  assert(!state.evaluation_simulation_output_enabled);
  assert(!state.topology_snapshot.simulated_output_enabled);
}
"""

for key, path, anchor in (
    ("__LEGACY_REAL__", "packages/inputs/real-time.yaml",
     "- id: capture_live_evaluation_snapshot"),
    ("__LEGACY_DEVELOPMENT__", "packages/inputs/development.yaml",
     "- id: capture_development_evaluation_snapshot"),
    ("__TOPOLOGY_REAL__", "packages/topology/input-real.yaml",
     "- id: capture_topology_real_snapshot"),
    ("__TOPOLOGY_DEVELOPMENT__", "packages/topology/input-development.yaml",
     "- id: capture_topology_development_snapshot"),
):
    source = source.replace(key, lambda_body(path, anchor))

with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / "seasonal_profile_parity.cpp"
    executable = Path(directory) / "seasonal_profile_parity"
    cpp.write_text(source)
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I",
         str(ROOT), str(cpp), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
print("Legacy and topology real/development snapshots are consistent")
