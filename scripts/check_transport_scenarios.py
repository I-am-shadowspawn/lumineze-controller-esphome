"""Run the production dispatcher lambdas against a simulated BLE transaction.

The C++ lambda bodies are read from the ESPHome YAML. This checks the actual
state transitions, while the BLE protocol and physical lamps remain mocked.
"""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def lambda_body(path: str, anchor: str, *, inside: bool = False) -> str:
    lines = (ROOT / path).read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if anchor in line)
    if inside:
        while "- lambda: |-" not in lines[start]:
            start -= 1
    else:
        while "- lambda: |-" not in lines[start]:
            start += 1
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = []
    for line in lines[start + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line[indent + 4 :])
    return "\n".join(body).replace("${enable_jungle_dawn}", "true").replace(
        "${enable_prot5}", "true"
    )


queue = lambda_body("packages/core/dispatcher.yaml", "- id: queue_lumenize_command")
failure = lambda_body("packages/core/dispatcher.yaml", "- id: record_ble_failure")
tick = lambda_body("packages/core/dispatcher.yaml", "- id: dispatcher_tick")
complete_jungle = lambda_body(
    "packages/lamps/protocol.yaml",
    "const int completed = id(lamp_inflight)[0];",
    inside=True,
)
complete_prot5 = lambda_body(
    "packages/lamps/protocol.yaml",
    "const int completed = id(lamp_inflight)[1];",
    inside=True,
)
protocol = (ROOT / "packages/lamps/protocol.yaml").read_text()
for lamp in (0, 1):
    assert (
        f"id(lamp_inflight_generation)[{lamp}] = "
        f"id(lamp_request_generation)[{lamp}];"
    ) in protocol

source = r"""
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
struct Text { void publish_state(const char*) {} void publish_state(const std::string&) {} };
struct Number { float state = 0; };
struct ClockNow {
  bool is_valid() const { return false; }
  std::string strftime(const char*) const { return ""; }
};
struct Clock { ClockNow now() const { return {}; } };
struct State {
  int lamp_target[2] = {0, 0}, lamp_inflight[2] = {0, 0};
  int lamp_last_completed[2] = {-1, -1}, lamp_last_reported[2] = {-1, -1};
  int lamp_attempts_for_request[2] = {0, 0};
  int lamp_consecutive_failures[2] = {0, 0};
  int lamp_completed_count[2] = {0, 0}, lamp_failure_count[2] = {0, 0};
  uint32_t lamp_request_generation[2] = {0, 0};
  uint32_t lamp_inflight_generation[2] = {0, 0};
  uint32_t lamp_last_attempt_ms[2] = {0, 0};
  uint32_t lamp_last_failure_ms[2] = {0, 0};
  uint32_t lamp_retry_delay_ms[2] = {0, 0};
  uint32_t global_last_attempt_ms = 0, transaction_started_ms = 0;
  bool lamp_pending[2] = {false, false};
  bool lamp_connected[2] = {false, false};
  bool lamp_readback_received[2] = {false, false};
  bool lamp_readback_fresh[2] = {false, false};
  bool lamp_ever_attempted[2] = {false, false};
  bool transaction_active = false, transaction_write_completed = false;
  bool any_attempted = false;
  int active_lamp = -1, next_lamp = 0, dispatch_choice = -1;
  Number ble_max_attempts{3}, ble_retry_base_delay{30};
  Number ble_min_lamp_interval{30}, ble_inter_lamp_quiet{5};
  Text jungle_dawn_dispatch_status, prot5_dispatch_status;
  Text jungle_dawn_readback_status, prot5_readback_status;
  Text jungle_dawn_last_completed_time, prot5_last_completed_time;
  Clock controller_time;
} state;
#define id(name) state.name
uint32_t now_ms = 100000;
uint32_t millis() { return now_ms; }
void queue(int lamp, int level) {
__QUEUE__
}
void fail(int lamp) {
__FAILURE__
}
void tick() {
__TICK__
}
void complete_jungle() {
__COMPLETE__
}
void complete_prot5() {
__COMPLETE_PROT5__
}
void start(int lamp) {
  id(transaction_active) = true;
  id(active_lamp) = lamp;
  id(lamp_inflight)[lamp] = id(lamp_target)[lamp];
  id(lamp_inflight_generation)[lamp] = id(lamp_request_generation)[lamp];
  id(lamp_attempts_for_request)[lamp]++;
  id(lamp_readback_fresh)[lamp] = false;
  id(lamp_ever_attempted)[lamp] = true;
  id(lamp_last_attempt_ms)[lamp] = now_ms;
  id(any_attempted) = true;
  id(global_last_attempt_ms) = now_ms;
}
int main() {
  // A newer request remains pending after the old transaction completes.
  queue(0, 40);
  start(0);
  queue(0, 60);
  complete_jungle();
  assert(id(lamp_pending)[0] && id(lamp_target)[0] == 60);
  assert(id(lamp_last_completed)[0] == 40);
  now_ms += 31000;
  tick();
  assert(id(dispatch_choice) == 0);
  start(0);
  complete_jungle();
  assert(!id(lamp_pending)[0] && id(lamp_last_completed)[0] == 60);

  // Cancelling an in-flight request cannot resurrect a pending write.
  queue(0, 80);
  start(0);
  id(lamp_request_generation)[0]++;
  id(lamp_pending)[0] = false;
  complete_jungle();
  assert(!id(lamp_pending)[0]);
  queue(0, 80);
  start(0);
  id(lamp_request_generation)[0]++;
  id(lamp_pending)[0] = false;
  fail(0);
  assert(!id(lamp_pending)[0]);

  // A failed old request retains a newer decision instead of retrying stale data.
  queue(0, 30);
  start(0);
  queue(0, 20);
  fail(0);
  assert(id(lamp_pending)[0] && id(lamp_target)[0] == 20);
  assert(id(lamp_attempts_for_request)[0] == 0);

  // An unavailable lamp leaves its last report untouched; the other can run.
  id(lamp_last_reported)[0] = 70;
  queue(1, 25);
  now_ms += 6000;
  tick();
  assert(id(dispatch_choice) == 1);
  assert(id(lamp_last_reported)[0] == 70 && !id(lamp_readback_fresh)[0]);
  start(1);
  complete_prot5();
  assert(!id(lamp_pending)[1] && id(lamp_last_completed)[1] == 25);
  return 0;
}
"""
for key, body in {
    "__QUEUE__": queue,
    "__FAILURE__": failure,
    "__TICK__": tick,
    "__COMPLETE__": complete_jungle,
    "__COMPLETE_PROT5__": complete_prot5,
}.items():
    source = source.replace(key, body)

with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / "transport.cpp"
    executable = Path(directory) / "transport"
    cpp.write_text(source)
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
print("Transport scenarios passed")
