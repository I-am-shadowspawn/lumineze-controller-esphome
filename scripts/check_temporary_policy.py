"""Run the production policy lambda with controlled seasonal inputs and BLE events."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / 'packages/topology/fixture-policy.yaml').read_text().splitlines()
start = next(i for i, line in enumerate(lines) if '- lambda: |-' in line)
end = next(i for i in range(start + 1, len(lines)) if lines[i] == 'number:')
body = '\n'.join(line[10:] for line in lines[start + 1:end])
source = r'''
#include <cassert>
#include "components/lumineze_topology/transport_logic.h"
using namespace lumineze_topology;
struct Number { float state; };
struct Toggle { bool state; };
struct State {
  bool topology_snapshot_valid = true, topology_grace_expired = false;
  EvaluationSnapshot topology_snapshot{2026, 100};
  Number topology_invalid_time_grace{60}, topology_recovery_interval{300},
         topology_max_attempts{3};
  Toggle topology_invalid_time_safety{true};
  GroupState topology_groups[1];
  ContextState topology_contexts[1];
  FixtureState topology_fixtures[2];
  DispatchState topology_dispatch;
} state;
#define id(name) state.name
struct GroupBinding { int context, role; };
struct FixtureBinding { int slot, group; };
constexpr int group_count = 1;
constexpr GroupBinding groups[] = {{0, 0}};
constexpr FixtureBinding fixtures[] = {{0, 0}, {1, 0}};
uint32_t now = 100000;
uint32_t millis() { return now; }
void status(int, const char*) {}
void readback_status(int, const char*) {}
void policy() {
__POLICY__
}
void curve(int target) {
  auto &c = state.topology_contexts[0];
  c.valid = true; c.peak[0] = 1; c.curve[0] = target / 100.0f;
  c.desired[0] = c.curve[0];
  policy();
}
void finish(int slot) {
  auto &f = state.topology_fixtures[slot];
  auto &d = state.topology_dispatch;
  begin_transaction(f, d, slot, now);
  f.reported = f.in_flight; f.readback_received = true;
  assert(complete_transaction(f, d, slot, d.token));
}
int main() {
  state.topology_groups[0].automatic = true;
  for (auto &f : state.topology_fixtures) {
    f.maximum = 100; f.calibration_ready = true;
  }
  auto &f = state.topology_fixtures[0];
  auto &other = state.topology_fixtures[1];
  auto &d = state.topology_dispatch;
  curve(20); finish(0); finish(1);
  assert(apply_daily_maximum(f, 60, 2026, 100));
  for (int level : {45, 60}) {
    curve(level); assert(f.target == level && f.pending); finish(0); finish(1);
  }
  for (int level : {65, 80, 75, 61}) {
    curve(level); assert(f.target == 60 && !f.pending);
    assert(other.target == level && other.pending); finish(1);
  }
  curve(59); assert(f.target == 59 && f.pending && f.temporary_mode == TEMPORARY_NONE);
  finish(0);
  // Correct an obsolete high in-flight write, without resetting retry budget.
  curve(80); begin_transaction(f, d, 0, now);
  assert(apply_daily_maximum(f, 60, 2026, 100));
  policy(); assert(f.target == 60 && f.pending);
  f.readback_received = true;
  assert(complete_transaction(f, d, 0, d.token));
  assert(f.completed == 80 && f.target == 60 && f.pending && !f.readback_fresh);
  auto generation = f.generation;
  policy(); assert(f.generation == generation);
  for (int attempt = 1; attempt <= 3; ++attempt) {
    begin_transaction(f, d, 0, now);
    fail_transaction(f, d, 0, d.token, now, 3, 30000);
    policy(); assert(f.generation == generation && f.attempts == attempt);
  }
  assert(!f.pending);
  now += 300000; policy(); assert(f.pending && f.generation != generation);
  finish(0);
  // Revoke and resume an under-cap write interrupted by Apply.
  cancel_temporary(f); curve(40); begin_transaction(f, d, 0, now);
  assert(apply_daily_maximum(f, 60, 2026, 100));
  curve(80); assert(f.target == 40 && f.pending);
  complete_transaction(f, d, 0, d.token);
  assert(f.pending && !f.readback_fresh); finish(0);
  // Fixed restart, expiry and higher-priority modes never revive old requests.
  assert(start_timed_fixed_level(f, 35, 900000, now));
  policy(); assert(f.target == 35 && f.source == TEMPORARY_FIXED); finish(0);
  curve(75); assert(f.target == 35 && !f.pending && other.target == 75);
  now += 900000; policy(); assert(f.target == 75 && f.pending);
  finish(0);
  assert(start_timed_fixed_level(f, 0, 900000, now)); policy();
  begin_transaction(f, d, 0, now);
  state.topology_groups[0].manual = true;
  state.topology_groups[0].manual_fraction = .5f;
  policy(); assert(f.target == 50 && f.source == GROUP_MANUAL && f.pending);
  f.readback_received = true; complete_transaction(f, d, 0, d.token);
  assert(f.target == 50 && f.pending && !f.readback_fresh);
  finish(0);
  state.topology_groups[0].manual = false;
  assert(start_timed_fixed_level(f, 35, 900000, now)); policy();
  begin_transaction(f, d, 0, now);
  state.topology_groups[0].automatic = false;
  policy(); assert(f.temporary_mode == TEMPORARY_NONE && !f.pending);
  assert(fail_transaction(f, d, 0, d.token, now, 3, 30000) == CANCELLED_FAILURE);
  assert(!f.pending);
  state.topology_groups[0].automatic = true;
  assert(start_timed_fixed_level(f, 35, 900000, now)); policy();
  begin_transaction(f, d, 0, now);
  state.topology_snapshot_valid = false;
  policy(); assert(f.temporary_mode == TEMPORARY_NONE && f.source == SAFETY &&
                   f.target == 0 && f.pending);
  f.readback_received = true; complete_transaction(f, d, 0, d.token);
  assert(f.target == 0 && f.pending && !f.readback_fresh); finish(0);
  state.topology_snapshot_valid = true;
  assert(apply_daily_maximum(f, 100, 2026, 100)); curve(75); finish(0);
  state.topology_snapshot.day_of_year++;
  policy(); assert(f.temporary_mode == TEMPORARY_NONE && !f.pending &&
                   f.temporary_status == TEMP_STATUS_INACTIVE);
  assert(start_timed_fixed_level(f, 35, 900000, now)); policy();
  begin_transaction(f, d, 0, now);
  now += 900000; policy();
  assert(f.target == 75 && f.source == AUTOMATIC && f.pending);
  f.readback_received = true; complete_transaction(f, d, 0, d.token);
  assert(f.completed == 35 && f.target == 75 && f.pending && !f.readback_fresh);
  finish(0);
  // A fresh high mismatch must survive activation revoking freshness.
  f.target = 40; f.completed = 40; f.reported = 80; f.readback_fresh = true;
  assert(apply_daily_maximum(f, 60, 2026, 101));
  assert(!f.readback_fresh && f.temporary_correction_required);
  curve(80); assert(f.target == 60 && f.pending &&
                   f.temporary_status == TEMP_STATUS_ENFORCING);
  begin_transaction(f, d, 0, now);
  complete_transaction(f, d, 0, d.token);  // write completed, response missing
  policy(); assert(!f.pending && f.temporary_status == TEMP_STATUS_ENFORCING);
  cancel_temporary(f);
  state.topology_contexts[0].simulated = true;
  state.topology_contexts[0].simulated_output_enabled = true;
  assert(start_timed_fixed_level(f, 35, 900000, now)); policy();
  assert(f.target_simulated && f.pending);
  begin_transaction(f, d, 0, now);
  state.topology_contexts[0].simulated_output_enabled = false;
  policy(); assert(!f.pending && !f.readback_fresh);
  fail_transaction(f, d, 0, d.token, now, 3, 30000);
  assert(!f.pending);
}
'''.replace('__POLICY__', body)
with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / 'policy.cpp'
    binary = Path(directory) / 'policy'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT), str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print('Temporary lighting production-policy scenarios passed')
