"""Exercise the production topology dispatcher timeout and cleanup lambda."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LINES = (ROOT / "packages/topology/dispatcher.yaml").read_text().splitlines()


def dispatcher_body():
    start = next(i for i, line in enumerate(LINES)
                 if line.strip() == "- id: dispatcher_tick")
    start = next(i for i in range(start, len(LINES))
                 if LINES[i].strip() == "- lambda: |-")
    indent = len(LINES[start]) - len(LINES[start].lstrip())
    body = []
    for line in LINES[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line[indent + 4:])
    return "\n".join(body)


source = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include "components/lumineze_topology/transport_logic.h"

struct Number { float state = 0; };
struct FailureScript {
  void execute(int slot, uint32_t token);
  FailureScript *operator->() { return this; }
};
namespace lumineze_topology {
struct Binding { int slot; };
constexpr Binding fixtures[] = {{0}, {1}};
extern int dispatched_slot;
void stop(int) {}
void disconnect(int) {}
void status(int, const char *) {}
void readback_status(int, const char *) {}
void dispatch(int slot, uint32_t) { dispatched_slot = slot; }
}
struct State {
  lumineze_topology::DispatchState topology_dispatch;
  lumineze_topology::FixtureState topology_fixtures[4];
  Number topology_max_attempts{3};
  Number topology_retry_base_delay{30};
  Number topology_inter_fixture_quiet{5};
  Number topology_min_fixture_interval{5};
  Number topology_transaction_timeout{25};
  FailureScript record_topology_failure;
} state;
namespace lumineze_topology {
int dispatched_slot = -1;
}
#define id(name) state.name
uint32_t now_ms = 26000;
uint32_t millis() { return now_ms; }
void FailureScript::execute(int slot, uint32_t token) {
  lumineze_topology::fail_transaction(
      state.topology_fixtures[slot], state.topology_dispatch, slot, token,
      now_ms, static_cast<int>(state.topology_max_attempts.state),
      static_cast<uint32_t>(state.topology_retry_base_delay.state * 1000));
}
void dispatcher_tick() {
__DISPATCHER__
}

int main() {
  using namespace lumineze_topology;
  auto &dispatcher = state.topology_dispatch;
  auto &timed_out = state.topology_fixtures[0];
  auto &next = state.topology_fixtures[1];
  dispatcher.active = true;
  dispatcher.active_slot = 0;
  dispatcher.token = 9;
  dispatcher.started_ms = 1000;
  dispatcher.ever_attempted = true;
  dispatcher.last_attempt_ms = 1000;
  timed_out.connected = true;
  timed_out.pending = true;
  timed_out.attempts = 1;
  timed_out.ever_attempted = true;
  timed_out.last_attempt_ms = 1000;
  next.pending = true;

  dispatcher_tick();
  assert(dispatcher.active && dispatcher.cleanup_pending);
  assert(dispatcher.cleanup_started_ms == 26000);
  assert(dispatched_slot == -1);

  now_ms += 4500;
  timed_out.connected = false;
  dispatcher_tick();
  assert(!dispatcher.active && timed_out.pending);
  assert(timed_out.retry_delay_ms == 30000);

  dispatcher_tick();
  assert(dispatched_slot == 1);
  assert(dispatcher.active && dispatcher.active_slot == 1);
}
"""

source = source.replace("__DISPATCHER__", dispatcher_body())
with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / "dispatcher_timeout.cpp"
    executable = Path(directory) / "dispatcher_timeout"
    cpp.write_text(source)
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I",
         str(ROOT), str(cpp), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
print("Topology dispatcher timeout cleanup handoff passed")
