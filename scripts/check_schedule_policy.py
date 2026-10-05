"""Execute the production schedule engine and shared fixture policy against T10."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def body(path, marker="- lambda: |-", indent=10):
    lines = (ROOT / path).read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if marker in line) + 1
    end = start
    while end < len(lines) and (not lines[end] or lines[end].startswith(" " * indent)):
        end += 1
    return "\n".join(line[indent:] for line in lines[start:end])

source = r'''
#include <cassert>
#include <iostream>
#include "components/lumineze_topology/schedule_store.h"
#include "components/lumineze_topology/transport_logic.h"
using namespace lumineze_topology;
struct Number { float state; }; struct Toggle { bool state; };
struct Backend {
 ScheduleRecord records[2]{}; bool present[2]{}; int writes = 0;
 bool read(int i, ScheduleRecord &r) { r=records[i]; return present[i]; }
 bool write(int i, const ScheduleRecord &r) { records[i]=r; present[i]=true; ++writes; return true; }
 bool flush() { return true; }
};
struct State {
 bool topology_snapshot_valid = true, topology_grace_expired = false;
 EvaluationSnapshot topology_snapshot{2026,100,365,720,true,false,false};
 Number topology_invalid_time_grace{60}, topology_recovery_interval{300}, topology_max_attempts{3};
 Toggle topology_invalid_time_safety{true};
 GroupState topology_groups[2]; ContextState topology_contexts[2];
 ScheduleContextState topology_schedule_contexts[2]; Backend backends[2];
 FixtureState topology_fixtures[4]; DispatchState topology_dispatch;
} state;
#define id(x) ::state.x
struct GroupBinding { int context, role; }; struct FixtureBinding { int slot, group; };
constexpr int context_count=2, group_count=2;
constexpr GroupBinding groups[]={{0,0},{1,0}};
constexpr FixtureBinding fixtures[]={{0,0},{3,1}};
constexpr uint8_t schedule_masks[]={3,1};
constexpr uint32_t schedule_fingerprints[]={1234,5678};
uint32_t now=100000; uint32_t millis() { return now; }
void status(int, const char*) {} void readback_status(int, const char*) {}
void group_controls_off(int) {} void fixture_control_off(int) {}
void engine() { __ENGINE__ }
void policy() { __POLICY__ }
void safe_off(int group_index) { __SAFE_OFF__ }
void tick(float minute) { state.topology_snapshot.minutes=minute; engine(); policy(); }
void stage(int context, int low, int high, ScheduleMode mode=STEP) {
 auto &c=state.topology_schedule_contexts[context];
 for (int r=0;r<2;++r) { if (!(schedule_masks[context] & (1<<r))) continue;
 c.staged[r].mode=mode; c.staged[r].points[0]={true,0,static_cast<float>(low)};
 c.staged[r].points[1]={true,720,static_cast<float>(high)}; }
}
ScheduleApplyResult apply(int context) {
 auto result=apply_schedule(state.topology_schedule_contexts[context],state.backends[context],schedule_fingerprints[context],schedule_masks[context]);
 if (result==APPLIED) { engine(); policy(); } return result;
}
void finish(int slot=0) {
 auto &f=state.topology_fixtures[slot]; auto &d=state.topology_dispatch;
 begin_transaction(f,d,slot,now); d.write_completed=true;
 record_readback(f,d,slot,f.in_flight); assert(complete_transaction(f,d,slot,d.token));
}
void reset() {
 state=State{};
 for (int slot : {0,3}) { auto &f=state.topology_fixtures[slot]; f.maximum=100; f.calibration_ready=true; }
 stage(0,50,51); stage(1,10,90); assert(apply(0)==APPLIED && apply(1)==APPLIED);
 for (auto &g:state.topology_groups) g.automatic=true;
 tick(0); finish(); finish(3);
}
void pass(const char *id) { std::cout << "PASS " << id << '\n'; }
int main() {
 reset(); auto &f=state.topology_fixtures[0]; auto &c=state.topology_schedule_contexts[0];
 tick(720); assert(f.target==51 && f.pending); auto generation=f.generation;
 f.attempts=2; tick(721); assert(f.generation==generation && f.attempts==2); pass("step-bypass");
 reset(); stage(0,50,100,LINEAR); assert(apply(0)==APPLIED); tick(14.4f);
 assert(f.target==50 && !f.pending); pass("linear-filter");
 reset(); stage(0,20,80); tick(720); apply(0); auto &d=state.topology_dispatch;
 begin_transaction(f,d,0,now); stage(0,20,40); apply(0); assert(f.target==40 && f.pending);
 d.write_completed=true; record_readback(f,d,0,80); complete_transaction(f,d,0,d.token);
 assert(f.completed==80 && f.target==40 && f.pending && !f.readback_fresh); pass("apply-revokes");
 reset(); stage(0,20,40); tick(720); apply(0); begin_transaction(f,d,0,now); generation=f.generation;
 c.staged[0].points[0].level=21; apply(0); assert(f.target==40 && f.pending && f.generation!=generation);
 d.write_completed=true; record_readback(f,d,0,40); complete_transaction(f,d,0,d.token);
 assert(f.pending && !f.readback_fresh); pass("apply-identical-pending");
 finish(); generation=f.generation; c.staged[0].points[0].level=22; apply(0);
 assert(!f.pending && f.generation==generation && f.readback_fresh); pass("apply-identical-confirmed");
 auto writes=state.backends[0].writes; auto revision=c.active.revision;
 apply(0); assert(state.backends[0].writes==writes && c.active.revision==revision && f.generation==generation); pass("apply-unchanged");
 c.staged[0].points[1].level=75; c.staged[1].points[1].minute=0;
 auto other=state.topology_fixtures[3].generation; auto other_revision=state.topology_contexts[1].revision;
 assert(apply(0)==INVALID_EDIT && c.active.revision==revision && f.generation==generation && c.active.roles[0].points[1].level==40); pass("atomic-context-rejection");
 assert(state.topology_fixtures[3].generation==other && state.topology_contexts[1].revision==other_revision); pass("independent-context");
 cancel_schedule_edits(c); c.staged[0].points[1].level=90; tick(720);
 assert(f.target==40 && schedule_dirty(c,3)); pass("staging-only");
 c.staged[0].points[1].level=80; apply(0); generation=f.generation;
 c.staged[0].points[1].level=70; cancel_schedule_edits(c);
 assert(!schedule_dirty(c,3) && f.pending && f.generation==generation); pass("cancel-edits");
 reset(); state.topology_snapshot.valid=false; stage(0,30,75); apply(0);
 assert(c.active.revision==2 && f.target==0 && f.source==SAFETY); pass("apply-invalid-clock");
 reset(); f.manual=true; f.manual_level=30; policy(); finish(); generation=f.generation;
 stage(0,20,75); apply(0); assert(f.target==30 && f.source==FIXTURE_MANUAL && f.generation==generation); pass("manual-priority");
 reset(); tick(720); begin_transaction(f,d,0,now); state.topology_groups[0].automatic=false; policy();
 generation=f.generation; complete_transaction(f,d,0,d.token); policy();
 assert(!f.pending && f.generation==generation && f.target==51); pass("automatic-off");
 reset(); tick(720); safe_off(0); policy();
 assert(!state.topology_groups[0].automatic && f.target==0 && f.pending && f.source==SAFETY); pass("safe-off");
 reset(); f.manual=true; f.manual_level=30; policy(); state.topology_snapshot.valid=false; engine(); policy();
 assert(f.source==SAFETY && f.target==0); pass("clock-loss");
 reset(); c=ScheduleContextState{}; f.manual=true; f.manual_level=30; tick(720);
 assert(!state.topology_contexts[0].valid && f.target==30 && f.source==FIXTURE_MANUAL); pass("invalid-schedule-manual");
 reset(); state.topology_groups[0].automatic=false; stage(0,20,80); apply(0);
 ScheduleContextState restored; assert(restore_schedule(restored,state.backends[0],schedule_fingerprints[0],3)); c=restored;
 tick(720); assert(state.topology_contexts[0].desired[0]==0.8f && !state.topology_groups[0].automatic && !f.pending); pass("startup-midday");
 state.topology_groups[0].automatic=true; tick(0); assert(f.target==20); tick(720); assert(f.target==80); pass("ha-disconnected");
 reset(); state.topology_snapshot.simulated=true; state.topology_snapshot.simulated_output_enabled=false;
 tick(720); assert(!f.pending && f.target==50 && state.topology_contexts[0].desired[0]==0.51f); pass("sim-output-disabled");
 state.topology_snapshot.simulated_output_enabled=true; tick(720); finish();
 state.topology_snapshot.simulated=false; tick(0); assert(f.pending && f.target==50 && !f.target_simulated); pass("sim-return-live");
 reset(); c.staged[0].points[2]={true,400,90}; c.staged[0].points[3]={true,600,20}; apply(0); finish();
 tick(800); assert(f.target==51); pass("skip-step-events");
 // Reduced calibration cannot be hidden by the ordinary threshold.
 reset(); stage(0,50,100); apply(0); tick(720); finish(); f.maximum=99; policy(); assert(f.pending && f.target==99);
}
'''
source = source.replace('__ENGINE__', body('packages/topology/schedule-engine.yaml'))
source = source.replace('__POLICY__', body('packages/topology/fixture-policy.yaml'))
source = source.replace('__SAFE_OFF__', body('packages/topology/safe-off.yaml'))
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'policy.cpp'; binary=Path(tmp)/'policy'; cpp.write_text(source)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(ROOT),str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
