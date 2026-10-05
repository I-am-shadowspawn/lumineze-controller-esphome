#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>

namespace lumineze_topology {

constexpr int SCHEDULE_POINTS = 8;
enum ScheduleMode : uint8_t { STEP = 0, LINEAR = 1, INVALID_MODE = 255 };

struct SchedulePoint {
  uint16_t minute = 0;
  uint8_t level = 0;
  bool enabled = false;
  constexpr SchedulePoint() = default;
  constexpr SchedulePoint(bool enabled, uint16_t minute, uint8_t level)
      : minute(minute), level(level), enabled(enabled) {}
};
static_assert(sizeof(SchedulePoint) == 4, "Bounded point storage budget changed");
struct ScheduleRole {
  ScheduleMode mode = STEP;
  std::array<SchedulePoint, SCHEDULE_POINTS> points{};
};
struct ScheduleInputPoint {
  bool enabled = false;
  float minute = 0;
  float level = 0;
};
struct ScheduleInput {
  ScheduleMode mode = STEP;
  std::array<ScheduleInputPoint, SCHEDULE_POINTS> points{};
  int count = SCHEDULE_POINTS;
};

enum ScheduleError : uint8_t {
  SCHEDULE_OK, BAD_CAPACITY, BAD_MODE, BAD_MINUTE, BAD_LEVEL,
  DUPLICATE_MINUTE, TOO_FEW_POINTS,
};

inline ScheduleMode schedule_mode(const char *mode) {
  if (std::strcmp(mode, "step") == 0) return STEP;
  if (std::strcmp(mode, "linear") == 0) return LINEAR;
  return INVALID_MODE;
}
inline int schedule_role(const char *role) {
  if (std::strcmp(role, "visible") == 0) return 0;
  if (std::strcmp(role, "uv") == 0) return 1;
  return -1;
}
inline bool whole_number(float value, float maximum) {
  return std::isfinite(value) && value >= 0 && value <= maximum &&
      value == std::floor(value);
}

// Conversion succeeds atomically: the destination remains unchanged on error.
// All fields, including disabled points, are validated before narrowing types.
inline ScheduleError validate_schedule(const ScheduleInput &input, bool used,
                                        ScheduleRole &destination) {
  if (input.count < 0 || input.count > SCHEDULE_POINTS) return BAD_CAPACITY;
  if (input.mode != STEP && input.mode != LINEAR) return BAD_MODE;
  ScheduleRole candidate;
  candidate.mode = input.mode;
  int enabled = 0;
  for (int index = 0; index < input.count; ++index) {
    const auto &point = input.points[index];
    if (!whole_number(point.minute, 1439)) return BAD_MINUTE;
    if (!whole_number(point.level, 100)) return BAD_LEVEL;
    candidate.points[index] = {point.enabled, static_cast<uint16_t>(point.minute),
                               static_cast<uint8_t>(point.level)};
    if (!point.enabled) continue;
    enabled++;
    for (int previous = 0; previous < index; ++previous)
      if (candidate.points[previous].enabled &&
          candidate.points[previous].minute == candidate.points[index].minute)
        return DUPLICATE_MINUTE;
  }
  if (used && enabled < 2) return TOO_FEW_POINTS;
  destination = used ? candidate : ScheduleRole{};
  return SCHEDULE_OK;
}

inline bool valid_schedule(const ScheduleRole &role, bool used) {
  ScheduleInput input;
  input.mode = role.mode;
  for (int index = 0; index < SCHEDULE_POINTS; ++index) {
    const auto &point = role.points[index];
    input.points[index] = {point.enabled, static_cast<float>(point.minute),
                           static_cast<float>(point.level)};
  }
  ScheduleRole ignored;
  return validate_schedule(input, used, ignored) == SCHEDULE_OK;
}

struct ScheduleResult {
  bool valid = false;
  float percent = 0;
  int segment = -1;  // Stable editor slot of the previous enabled point.
};

inline ScheduleResult evaluate_schedule(const ScheduleRole &role, bool used,
                                        float minute, bool snapshot_valid = true) {
  ScheduleResult result;
  if (!used || !snapshot_valid || !std::isfinite(minute) || minute < 0 ||
      minute >= 1440 || !valid_schedule(role, true)) return result;
  std::array<int, SCHEDULE_POINTS> ordered{};
  int count = 0;
  for (int slot = 0; slot < SCHEDULE_POINTS; ++slot)
    if (role.points[slot].enabled) ordered[count++] = slot;
  std::sort(ordered.begin(), ordered.begin() + count, [&role](int a, int b) {
    return role.points[a].minute < role.points[b].minute;
  });
  int previous = count - 1;
  for (int index = 0; index < count; ++index) {
    if (role.points[ordered[index]].minute <= minute) previous = index;
    else break;
  }
  const int next = (previous + 1) % count;
  const auto &a = role.points[ordered[previous]];
  const auto &b = role.points[ordered[next]];
  result.valid = true;
  result.segment = ordered[previous];
  result.percent = a.level;
  if (role.mode == LINEAR) {
    float start = a.minute;
    float end = b.minute;
    if (previous == count - 1) {
      if (minute < start) start -= 1440;
      else end += 1440;
    }
    result.percent = a.level + (static_cast<float>(b.level) - a.level) *
        ((minute - start) / (end - start));
  }
  return result;
}

}  // namespace lumineze_topology
