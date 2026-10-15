"""Exercise the actual Apply/Cancel action lambdas with a bounded host backend."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "packages/topology/context-schedule.yaml").read_text().splitlines()

def action(identity):
    begin = next(i for i, line in enumerate(lines) if f"id: ${{context_id}}_{identity}" in line)
    start = next(i for i in range(begin, len(lines)) if "- lambda: |-" in lines[i]) + 1
    end = start
    while end < len(lines) and (not lines[end] or lines[end].startswith("          ")):
        end += 1
    return "\n".join(line[10:] for line in lines[start:end]).replace("${context_id}", "shared")

source = r'''
#include <cassert>
#include "components/lumineze_topology/schedule_store.h"
using namespace lumineze_topology;
struct Backend {
  ScheduleRecord records[2]{}; bool present[2]{}; int writes = 0;
  bool read(int i, ScheduleRecord &r) { r = records[i]; return present[i]; }
  bool write(int i, const ScheduleRecord &r) { records[i] = r; present[i] = true; ++writes; return true; }
  bool flush() { return true; }
};
struct Script { int calls = 0; void execute() { ++calls; } };
struct State { ScheduleContextState topology_schedule_contexts[1]; Backend topology_schedule_preferences[1]; Script evaluate_topology; } state;
#define id(x) ::state.x
constexpr uint32_t schedule_fingerprints[] = {1234};
constexpr uint8_t schedule_masks[] = {3};
int context_index(const char*) { return 0; }
int publications = 0;
void publish_schedule_staging(int) { ++publications; }
void apply() { __APPLY__ }
void cancel() { __CANCEL__ }
int main() {
 auto &c = state.topology_schedule_contexts[0];
 apply(); assert(c.last_apply == INVALID_EDIT && !c.configured && state.evaluate_topology.calls == 0);
 for (auto &role : c.staged) { role.points[0] = {true, 0, 20}; role.points[1] = {true, 720, 80}; }
 assert(!c.configured && state.evaluate_topology.calls == 0);
 apply(); assert(c.configured && c.active.revision == 1 && state.evaluate_topology.calls == 1);
 apply(); assert(c.last_apply == UNCHANGED && state.evaluate_topology.calls == 1 && state.topology_schedule_preferences[0].writes == 1);
 c.staged[0].points[1].level = 40; c.staged[1].points[1].minute = 0;
 apply(); assert(c.last_apply == INVALID_EDIT && c.error_role == 1 && c.error_point == 1 && c.active.revision == 1 && state.evaluate_topology.calls == 1);
 cancel(); assert(publications == 1 && !schedule_dirty(c, 3) && c.staged[0].points[1].level == 80 && state.evaluate_topology.calls == 1);
}
'''.replace("__APPLY__", action("apply_schedule")).replace("__CANCEL__", action("cancel_schedule_edits"))
with tempfile.TemporaryDirectory() as tmp:
    cpp = Path(tmp) / "editor.cpp"
    binary = Path(tmp) / "editor"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT), str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("PASS actual schedule Apply/Cancel actions: staging, rejection, unchanged and publication")
