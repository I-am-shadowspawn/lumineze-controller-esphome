#pragma once

#include "schedule_logic.h"

namespace lumineze_topology {

using ScheduleRecord = std::array<uint8_t, 87>;
struct ScheduleSnapshot {
  std::array<ScheduleRole, 2> roles{};
  uint32_t revision = 0;
  uint32_t fingerprint = 0;
  uint8_t used_roles = 0;
};
enum ScheduleApplyResult : uint8_t {
  APPLIED, UNCHANGED, INVALID_EDIT, WRITE_FAILED, STORAGE_UNKNOWN,
};
struct ScheduleContextState {
  std::array<ScheduleInput, 2> staged{};
  ScheduleSnapshot active{};
  bool configured = false;
  bool storage_locked = false;
  int active_bank = -1;
  ScheduleApplyResult last_apply = UNCHANGED;
  ScheduleError error = SCHEDULE_OK;
  int error_role = -1;
  int error_point = -1;
  uint32_t evaluated_revision = 0;
  bool evaluated_valid = false;
  bool evaluated_simulated = false;
  int last_segment[2] = {-1, -1};
};

inline void put_u16(ScheduleRecord &record, int offset, uint16_t value) {
  record[offset] = value & 255;
  record[offset + 1] = value >> 8;
}
inline uint16_t get_u16(const ScheduleRecord &record, int offset) {
  return record[offset] | static_cast<uint16_t>(record[offset + 1]) << 8;
}
inline void put_u32(ScheduleRecord &record, int offset, uint32_t value) {
  for (int byte = 0; byte < 4; ++byte) record[offset + byte] = value >> (byte * 8);
}
inline uint32_t get_u32(const ScheduleRecord &record, int offset) {
  uint32_t value = 0;
  for (int byte = 0; byte < 4; ++byte)
    value |= static_cast<uint32_t>(record[offset + byte]) << (byte * 8);
  return value;
}
inline uint32_t schedule_crc(const ScheduleRecord &record) {
  uint32_t crc = UINT32_MAX;
  for (int index = 0; index < 83; ++index) {
    crc ^= record[index];
    for (int bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ ((crc & 1) ? 0xEDB88320U : 0U);
  }
  return ~crc;
}
inline ScheduleRecord encode_schedule(const ScheduleSnapshot &snapshot) {
  ScheduleRecord record{};
  record[0] = 'L'; record[1] = 'Z'; record[2] = 'S'; record[3] = 'C';
  put_u16(record, 4, 1);
  put_u16(record, 6, 87);
  put_u32(record, 8, snapshot.revision);
  put_u32(record, 12, snapshot.fingerprint);
  record[16] = snapshot.used_roles;
  for (int role = 0; role < 2; ++role) {
    const int base = 17 + role * 33;
    record[base] = snapshot.roles[role].mode;
    for (int slot = 0; slot < 8; ++slot) {
      const int offset = base + 1 + slot * 4;
      const auto &point = snapshot.roles[role].points[slot];
      record[offset] = point.enabled;
      put_u16(record, offset + 1, point.minute);
      record[offset + 3] = point.level;
    }
  }
  put_u32(record, 83, schedule_crc(record));
  return record;
}
inline bool decode_schedule(const ScheduleRecord &record, uint32_t fingerprint,
                            uint8_t used_roles, ScheduleSnapshot &destination) {
  if (record[0] != 'L' || record[1] != 'Z' || record[2] != 'S' || record[3] != 'C' ||
      get_u16(record, 4) != 1 || get_u16(record, 6) != 87 ||
      get_u32(record, 8) == 0 || get_u32(record, 12) != fingerprint ||
      !used_roles || used_roles > 3 || record[16] != used_roles ||
      get_u32(record, 83) != schedule_crc(record)) return false;
  ScheduleSnapshot candidate;
  candidate.revision = get_u32(record, 8);
  candidate.fingerprint = fingerprint;
  candidate.used_roles = used_roles;
  for (int role = 0; role < 2; ++role) {
    const int base = 17 + role * 33;
    candidate.roles[role].mode = static_cast<ScheduleMode>(record[base]);
    for (int slot = 0; slot < 8; ++slot) {
      const int offset = base + 1 + slot * 4;
      if (record[offset] > 1) return false;
      candidate.roles[role].points[slot] = {
          record[offset] != 0, get_u16(record, offset + 1), record[offset + 3]};
    }
    const bool used = used_roles & (1 << role);
    if (!valid_schedule(candidate.roles[role], used)) return false;
    if (!used) {
      if (candidate.roles[role].mode != STEP) return false;
      for (const auto &point : candidate.roles[role].points)
        if (point.enabled || point.minute || point.level) return false;
    }
  }
  destination = candidate;
  return true;
}

inline bool same_schedule(const ScheduleSnapshot &a, const ScheduleSnapshot &b) {
  auto comparison = a;
  comparison.revision = b.revision;
  return encode_schedule(comparison) == encode_schedule(b);
}
inline void cancel_schedule_edits(ScheduleContextState &context) {
  for (int role = 0; role < 2; ++role) {
    context.staged[role] = ScheduleInput{};
    if (!context.configured) continue;
    const auto &active = context.active.roles[role];
    context.staged[role].mode = active.mode;
    for (int slot = 0; slot < 8; ++slot) {
      const auto &point = active.points[slot];
      context.staged[role].points[slot] = {point.enabled,
          static_cast<float>(point.minute), static_cast<float>(point.level)};
    }
  }
  context.error = SCHEDULE_OK;
  context.error_role = -1;
  context.error_point = -1;
  context.last_apply = context.storage_locked ? STORAGE_UNKNOWN : UNCHANGED;
}
inline bool schedule_dirty(const ScheduleContextState &context, uint8_t used_roles) {
  for (int role = 0; role < 2; ++role) {
    if (!(used_roles & (1 << role))) continue;
    const auto &input = context.staged[role];
    const auto &active = context.active.roles[role];
    if (input.mode != (context.configured ? active.mode : STEP)) return true;
    for (int slot = 0; slot < 8; ++slot) {
      const auto &p = input.points[slot];
      const SchedulePoint reference = context.configured ? active.points[slot] : SchedulePoint{};
      if (p.enabled != reference.enabled || p.minute != reference.minute ||
          p.level != reference.level) return true;
    }
  }
  return false;
}

// Backend contract: read(bank, record), write(bank, record), flush().
// write false means definitely not queued; flush/read failure is uncertain.
template<typename Backend>
bool restore_schedule(ScheduleContextState &context, Backend &backend,
                      uint32_t fingerprint, uint8_t used_roles) {
  ScheduleRecord records[2];
  ScheduleSnapshot snapshots[2];
  bool valid[2];
  for (int bank = 0; bank < 2; ++bank)
    valid[bank] = backend.read(bank, records[bank]) &&
        decode_schedule(records[bank], fingerprint, used_roles, snapshots[bank]);
  int selected = valid[0] ? 0 : valid[1] ? 1 : -1;
  if (valid[0] && valid[1]) {
    const uint32_t delta = snapshots[1].revision - snapshots[0].revision;
    if ((delta == 0 && records[0] != records[1]) || delta == 0x80000000U)
      selected = -1;
    else if (delta > 0 && delta < 0x80000000U) selected = 1;
  }
  context = ScheduleContextState{};
  if (selected >= 0) {
    context.active = snapshots[selected];
    context.active_bank = selected;
    context.configured = true;
  }
  cancel_schedule_edits(context);
  return context.configured;
}

template<typename Backend>
ScheduleApplyResult apply_schedule(ScheduleContextState &context, Backend &backend,
                                  uint32_t fingerprint, uint8_t used_roles) {
  if (context.storage_locked) return context.last_apply = STORAGE_UNKNOWN;
  ScheduleSnapshot candidate;
  candidate.fingerprint = fingerprint;
  candidate.used_roles = used_roles;
  if (!used_roles || used_roles > 3) return context.last_apply = INVALID_EDIT;
  for (int role = 0; role < 2; ++role) {
    const auto error = validate_schedule(context.staged[role], used_roles & (1 << role),
                                         candidate.roles[role], &context.error_point);
    if (error != SCHEDULE_OK) {
      context.error = error;
      context.error_role = role;
      return context.last_apply = INVALID_EDIT;
    }
  }
  context.error = SCHEDULE_OK;
  context.error_role = -1;
  context.error_point = -1;
  if (context.configured && same_schedule(candidate, context.active))
    return context.last_apply = UNCHANGED;
  candidate.revision = context.active.revision + 1;
  if (!candidate.revision) candidate.revision = 1;
  const int bank = context.active_bank == 0 ? 1 : 0;
  const auto encoded = encode_schedule(candidate);
  if (!backend.write(bank, encoded)) return context.last_apply = WRITE_FAILED;
  ScheduleRecord verified;
  if (!backend.flush() || !backend.read(bank, verified) || verified != encoded) {
    context.storage_locked = true;
    return context.last_apply = STORAGE_UNKNOWN;
  }
  context.active = candidate;
  context.active_bank = bank;
  context.configured = true;
  context.last_apply = APPLIED;
  return APPLIED;
}

}  // namespace lumineze_topology
