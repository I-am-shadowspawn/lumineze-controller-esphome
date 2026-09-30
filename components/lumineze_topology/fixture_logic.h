#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

#include "runtime_types.h"

namespace lumineze_topology {

inline bool automatic_output_allowed(bool simulated, bool bench_enabled) {
  return !simulated || bench_enabled;
}

inline bool invalid_real_clock(bool snapshot_valid, bool simulated) {
  return !snapshot_valid && !simulated;
}

inline bool automatic_refresh_required(bool previous_simulated,
                                       bool simulated) {
  return previous_simulated && !simulated;
}

inline void update_group_demand(GroupState &group, float demand, bool valid) {
  if (!valid) return;
  if (group.demand != demand) group.revision++;
  group.demand = demand;
}

inline Source resolve_source(bool safety_active, bool fixture_manual,
                             Source group_source) {
  if (safety_active) return SAFETY;
  if (fixture_manual) return FIXTURE_MANUAL;
  if (group_source == GROUP_MANUAL || group_source == AUTOMATIC)
    return group_source;
  return HOLD;
}

// Pure fixture-boundary conversion. The engine supplies fractions; only this
// function sees a physical maximum and produces an integer lamp command.
struct ConversionInput {
  Source source;
  float maximum;
  float demand;
  float peak;
  float curve;
  int manual_level;
  int previous_target;
  int minimum_change;
  bool automatic_queued;
  bool cap_reduced;
  bool previous_invalid;
  bool recovery_due;
  bool source_changed;
};

struct ConversionResult {
  bool valid = false;
  bool submit = false;
  bool limit_applied = false;
  int target = 0;
};

inline ConversionResult convert_fixture(const ConversionInput &input) {
  ConversionResult result;
  if (input.source == HOLD) return result;
  const bool cap_valid = std::isfinite(input.maximum) &&
      input.maximum >= 0.0f && input.maximum <= 100.0f;
  const float cap = cap_valid ? input.maximum : 0.0f;
  int peak_target = 0;
  if (input.source == SAFETY) {
    result.target = 0;
  } else if (input.source == FIXTURE_MANUAL) {
    const int requested = std::max(0, std::min(100, input.manual_level));
    if (!cap_valid && requested > 0) return result;
    result.target = std::min(requested, static_cast<int>(std::lround(cap)));
    result.limit_applied = result.target < requested;
  } else if (input.source == GROUP_MANUAL) {
    if (!std::isfinite(input.demand) || input.demand < 0.0f ||
        input.demand > 1.0f || (!cap_valid && input.demand > 0.0f))
      return result;
    result.target = std::max(0, std::min(100, static_cast<int>(
        std::lround(cap * input.demand))));
    result.limit_applied = result.target < static_cast<int>(
        std::lround(100.0f * input.demand));
  } else if (input.source == AUTOMATIC) {
    if (!std::isfinite(input.demand) || !std::isfinite(input.peak) ||
        !std::isfinite(input.curve) || input.demand < 0.0f ||
        input.demand > input.peak || input.peak > 1.0f ||
        input.peak < 0.0f || input.curve < 0.0f ||
        input.curve > 1.0f || (!cap_valid && input.demand > 0.0f))
      return result;
    // Preserve T06's float operation order and peak rounding.
    const float effective_peak = cap * input.peak;
    peak_target = static_cast<int>(std::lround(effective_peak));
    result.target = std::max(0, std::min(peak_target, static_cast<int>(
        std::lround(effective_peak * input.curve))));
    result.limit_applied = result.target < static_cast<int>(
        std::lround(100.0f * input.demand));
  } else {
    return result;
  }
  result.valid = true;
  const bool changed = result.target != input.previous_target;
  result.submit = input.source_changed || input.recovery_due;
  if (input.source == AUTOMATIC && changed) {
    const bool endpoint = result.target == 0 || result.target == peak_target;
    const bool threshold = std::abs(result.target - input.previous_target) >=
        std::max(1, input.minimum_change);
    result.submit = result.submit || !input.automatic_queued || endpoint ||
        threshold || ((input.cap_reduced || input.previous_invalid) &&
                      result.target < input.previous_target);
  } else if (changed) {
    result.submit = true;
  }
  return result;
}

inline bool elapsed(uint32_t now, uint32_t since, uint32_t duration) {
  return static_cast<uint32_t>(now - since) >= duration;
}

inline int select_due_slot(int next_slot, const bool enabled[4],
                           const bool due[4]) {
  for (int offset = 0; offset < 4; ++offset) {
    const int slot = (next_slot + offset) % 4;
    if (enabled[slot] && due[slot]) return slot;
  }
  return -1;
}

inline bool owns_transaction(const DispatchState &dispatcher, int slot,
                             uint32_t token) {
  return dispatcher.active && dispatcher.active_slot == slot &&
      dispatcher.token == token;
}

}  // namespace lumineze_topology
