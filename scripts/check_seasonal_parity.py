"""Compile the production seasonal lambda against a v1 target corpus."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LINES = (ROOT / "packages/topology/seasonal-engine.yaml").read_text().splitlines()
start = next(index for index, line in enumerate(LINES) if line.strip() == "- id: evaluate_topology")
start = next(index for index in range(start, len(LINES)) if LINES[index].strip() == "- lambda: |-")
indent = len(LINES[start]) - len(LINES[start].lstrip())
body = []
for line in LINES[start + 1 :]:
    if line.strip() and len(line) - len(line.lstrip()) <= indent:
        break
    body.append(line[indent + 4 :])
production_lambda = "\n".join(body)

source = r"""
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <utility>
#include "components/lumineze_topology/fixture_logic.h"

namespace lumineze_topology { constexpr int context_count = 2; }
struct ClockValue {
  bool valid = true;
  int year = 2026, day_of_year = 172, hour = 12, minute = 30, second = 0;
  bool is_valid() const { return valid; }
};
struct Clock { ClockValue value; ClockValue now() const { return value; } };
struct State {
  Clock controller_time;
  bool topology_snapshot_valid = false;
  lumineze_topology::ContextState topology_contexts[2];
} state;
#define id(name) state.name
void evaluate() {
__PRODUCTION__
}

std::pair<int, int> legacy_targets(const ClockValue &clock,
                                   const lumineze_topology::ContextState &settings,
                                   float visible_cap, float uv_cap) {
  constexpr float pi = 3.14159265358979323846f;
  constexpr float deg_to_rad = pi / 180.0f;
  const int year = clock.year;
  const int days = (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0))
      ? 366 : 365;
  float day = std::fmod(static_cast<float>(clock.day_of_year - 1) +
                           settings.phase_days, static_cast<float>(days));
  if (day < 0.0f) day += days;
  day += 1.0f;
  const float gamma = 2.0f * pi / static_cast<float>(days) * (day - 1.0f);
  const float decl = 0.006918f - 0.399912f * std::cos(gamma) +
      0.070257f * std::sin(gamma) - 0.006758f * std::cos(2.0f * gamma) +
      0.000907f * std::sin(2.0f * gamma) -
      0.002697f * std::cos(3.0f * gamma) +
      0.001480f * std::sin(3.0f * gamma);
  const float latitude = settings.latitude * deg_to_rad;
  const auto length = [latitude, pi](float declination) {
    const float cosine = -std::tan(latitude) * std::tan(declination);
    const float angle = cosine >= 1.0f ? 0.0f :
        cosine <= -1.0f ? pi : std::acos(cosine);
    return 24.0f * angle / pi;
  };
  const float hours = length(decl);
  const float noon = settings.noon_minutes;
  const float sunrise = noon - hours * 30.0f;
  const float sunset = noon + hours * 30.0f;
  const float minutes = static_cast<float>(clock.hour * 60 + clock.minute) +
      static_cast<float>(clock.second) / 60.0f;
  float visible_envelope = 0.0f;
  if (sunset > sunrise && minutes > sunrise && minutes < sunset) {
    const float progress = (minutes - sunrise) / (sunset - sunrise);
    visible_envelope = std::max(0.0f,
        std::min(1.0f, std::sin(pi * progress)));
  }
  const float tilt = 23.4393f * deg_to_rad;
  const float shortest = std::min(length(tilt), length(-tilt));
  const float longest = std::max(length(tilt), length(-tilt));
  float season = 0.5f;
  if (longest - shortest > 0.001f)
    season = (hours - shortest) / (longest - shortest);
  season = std::max(0.0f, std::min(1.0f, season));
  const float visible_scale = settings.visible_winter +
      (settings.visible_summer - settings.visible_winter) * season;
  const float visible_peak = visible_cap * visible_scale;
  const int visible_peak_target = static_cast<int>(std::lround(visible_peak));
  const float visible_curve = std::pow(visible_envelope,
      settings.visible_exponent);
  const int visible_target = std::max(0, std::min(visible_peak_target,
      static_cast<int>(std::lround(visible_peak * visible_curve))));
  const float uv_start = sunrise + settings.uv_start_minutes;
  const float uv_end = sunset - settings.uv_end_minutes;
  const float uv_window = std::max(0.0f, uv_end - uv_start);
  float uv_envelope = 0.0f;
  if (uv_window > 0.0f && minutes > uv_start && minutes < uv_end) {
    const float progress = (minutes - uv_start) / uv_window;
    uv_envelope = std::max(0.0f, std::min(1.0f, std::sin(pi * progress)));
  }
  const float uv_scale = settings.uv_winter +
      (settings.uv_summer - settings.uv_winter) * season;
  const float uv_peak = uv_cap * uv_scale;
  const int uv_peak_target = static_cast<int>(std::lround(uv_peak));
  const float uv_curve = std::pow(uv_envelope, settings.uv_exponent);
  const int uv_target = std::max(0, std::min(uv_peak_target,
      static_cast<int>(std::lround(uv_peak * uv_curve))));
  return {visible_target, uv_target};
}

int main() {
  auto &other = state.topology_contexts[1];
  other.latitude = 12.0f;
  other.phase_days = 75.0f;
  other.visible_winter = 0.45f;
  other.uv_start_minutes = 120.0f;
  int cases = 0;
  for (int year : {2024, 2026}) {
    const int last_day = year == 2024 ? 366 : 365;
    for (int day : {1, 80, 172, 266, last_day}) {
      for (int minute : {0, 300, 420, 600, 750, 900, 1080, 1439}) {
        state.controller_time.value = {true, year, day, minute / 60, minute % 60, 0};
        evaluate();
        for (int context_index = 0; context_index < 2; ++context_index) {
          const auto &context = state.topology_contexts[context_index];
          assert(context.valid);
          for (float cap : {0.0f, 1.0f, 59.0f, 60.0f, 100.0f}) {
            const auto expected = legacy_targets(
                state.controller_time.value, context, cap, cap);
            for (int role = 0; role < 2; ++role) {
              const lumineze_topology::ConversionInput input{
                  lumineze_topology::AUTOMATIC, cap, context.desired[role],
                  context.peak[role], context.curve[role], 0, -1, 2,
                  false, false, false, false, true};
              const auto actual = lumineze_topology::convert_fixture(input);
              assert(actual.valid);
              assert(actual.target == (role == 0 ? expected.first : expected.second));
              cases++;
            }
          }
        }
      }
    }
  }
  state.controller_time.value.valid = false;
  evaluate();
  assert(!state.topology_snapshot_valid);
  assert(!state.topology_contexts[0].valid && !state.topology_contexts[1].valid);
  assert(cases == 1600);
}
"""

with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / "seasonal.cpp"
    executable = Path(directory) / "seasonal"
    cpp.write_text(source.replace("__PRODUCTION__", production_lambda))
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT),
         str(cpp), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
print("Seasonal production lambda matches 1,600 v1 integer targets")
