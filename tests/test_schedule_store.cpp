#include <cassert>
#include <fstream>
#include <iostream>
#include "../components/lumineze_topology/schedule_store.h"

using namespace lumineze_topology;
struct Backend {
  ScheduleRecord durable[2]{};
  bool exists[2] = {false, false};
  ScheduleRecord queued{};
  int queued_bank = -1;
  int writes = 0;
  bool reject_write = false, uncertain_flush = false, read_failure = false;
  bool read(int bank, ScheduleRecord &record) {
    if (!exists[bank] || read_failure) return false;
    record = durable[bank]; return true;
  }
  bool write(int bank, const ScheduleRecord &record) {
    if (reject_write) return false;
    writes++; queued_bank = bank; queued = record; return true;
  }
  bool flush() {
    // An uncertain flush may have durably written: it cannot claim rejection.
    durable[queued_bank] = queued; exists[queued_bank] = true;
    queued_bank = -1;
    return !uncertain_flush;
  }
};
constexpr uint32_t fingerprint = 0x11223344;
void stage(ScheduleContextState &context) {
  for (auto &role : context.staged) {
    role.mode = LINEAR;
    role.points[0] = {true, 0, 0};
    role.points[1] = {true, 720, 100};
  }
}
int main(int argc, char **argv) {
  Backend backend;
  ScheduleContextState context;
  assert(!restore_schedule(context, backend, fingerprint, 3));
  assert(!context.configured && context.active.revision == 0 && !schedule_dirty(context, 3));
  stage(context);
  assert(schedule_dirty(context, 3));
  assert(apply_schedule(context, backend, fingerprint, 3) == APPLIED);
  assert(context.active.revision == 1 && context.active_bank == 0 && !schedule_dirty(context, 3));
  const auto first = backend.durable[0];
  assert(get_u16(first, 6) == 87 && get_u32(first, 12) == fingerprint);
  assert(apply_schedule(context, backend, fingerprint, 3) == UNCHANGED && backend.writes == 1);
  // Context-atomic rejection: a valid visible edit plus invalid UV duplicate.
  context.staged[0].points[1].level = 75;
  context.staged[1].points[1].minute = 0;
  assert(apply_schedule(context, backend, fingerprint, 3) == INVALID_EDIT);
  assert(context.error_role == 1 && context.error == DUPLICATE_MINUTE);
  assert(context.active.roles[0].points[1].level == 100 && backend.writes == 1);
  cancel_schedule_edits(context);
  assert(!schedule_dirty(context, 3) && context.error == SCHEDULE_OK);
  context.staged[0].points[1].level = 75;
  assert(apply_schedule(context, backend, fingerprint, 3) == APPLIED);
  assert(context.active.revision == 2 && context.active_bank == 1);
  ScheduleContextState reboot;
  assert(restore_schedule(reboot, backend, fingerprint, 3));
  assert(reboot.active.revision == 2 && !schedule_dirty(reboot, 3));
  // Uncommitted editor changes do not survive reboot.
  reboot.staged[0].points[1].level = 10;
  assert(restore_schedule(reboot, backend, fingerprint, 3));
  assert(reboot.staged[0].points[1].level == 75);
  // Corrupt newest falls back to older; every byte is covered by validation/CRC.
  backend.durable[1][30] ^= 1;
  assert(restore_schedule(reboot, backend, fingerprint, 3) && reboot.active.revision == 1);
  for (int offset = 0; offset < 87; ++offset) {
    auto corrupt = first; corrupt[offset] ^= 1;
    ScheduleSnapshot ignored;
    assert(!decode_schedule(corrupt, fingerprint, 3, ignored));
  }
  // Every possible torn prefix of a replacement bank recovers old or full new.
  auto next_snapshot = context.active;
  const auto replacement = encode_schedule(next_snapshot);
  for (int bytes = 0; bytes <= 87; ++bytes) {
    Backend torn;
    torn.durable[0] = first; torn.exists[0] = true;
    std::copy(replacement.begin(), replacement.begin() + bytes, torn.durable[1].begin());
    torn.exists[1] = bytes > 0;
    ScheduleContextState recovered;
    assert(restore_schedule(recovered, torn, fingerprint, 3));
    assert(recovered.active.revision == (bytes == 87 ? 2U : 1U));
  }
  // Even correctly checksummed malformed fields are rejected.
  for (int offset : {17, 18, 20, 21}) {
    auto corrupt = first;
    corrupt[offset] = 255;
    put_u32(corrupt, 83, schedule_crc(corrupt));
    ScheduleSnapshot ignored;
    assert(!decode_schedule(corrupt, fingerprint, 3, ignored));
  }
  auto wrong_schema = first; put_u16(wrong_schema, 4, 2);
  put_u32(wrong_schema, 83, schedule_crc(wrong_schema));
  backend.durable[0] = wrong_schema; backend.exists[1] = false;
  assert(!restore_schedule(reboot, backend, fingerprint, 3));
  backend.durable[0] = first;
  assert(!restore_schedule(reboot, backend, fingerprint + 1, 3));
  assert(!restore_schedule(reboot, backend, fingerprint, 1));
  assert(restore_schedule(reboot, backend, fingerprint, 3)); // unchanged ID/mask, label irrelevant
  // A definite failed write keeps active state, while uncertain flush locks Apply.
  reboot.staged[0].points[1].level = 80;
  backend.reject_write = true;
  assert(apply_schedule(reboot, backend, fingerprint, 3) == WRITE_FAILED);
  assert(reboot.active.revision == 1 && !reboot.storage_locked);
  backend.reject_write = false; backend.uncertain_flush = true;
  assert(apply_schedule(reboot, backend, fingerprint, 3) == STORAGE_UNKNOWN);
  assert(reboot.active.revision == 1 && reboot.storage_locked);
  int writes = backend.writes;
  cancel_schedule_edits(reboot);
  assert(reboot.storage_locked && apply_schedule(reboot, backend, fingerprint, 3) == STORAGE_UNKNOWN);
  assert(backend.writes == writes);
  assert(restore_schedule(reboot, backend, fingerprint, 3) && reboot.active.revision == 2);
  // Readback failure after a successful write is also uncertain, not success.
  backend.uncertain_flush = false; backend.read_failure = true;
  reboot.staged[0].points[1].level = 85;
  assert(apply_schedule(reboot, backend, fingerprint, 3) == STORAGE_UNKNOWN);
  assert(reboot.storage_locked && reboot.active.revision == 2);
  backend.read_failure = false;
  assert(restore_schedule(reboot, backend, fingerprint, 3) && reboot.active.revision == 3);
  // Revision rollover uses modulo order; ambiguous/equal conflicting banks reject.
  auto old = reboot.active; old.revision = UINT32_MAX;
  auto newer = old; newer.revision = 1;
  backend.durable[0] = encode_schedule(old); backend.durable[1] = encode_schedule(newer);
  backend.exists[0] = backend.exists[1] = true;
  assert(restore_schedule(reboot, backend, fingerprint, 3) && reboot.active.revision == 1);
  newer.revision = old.revision; newer.roles[0].points[1].level = 90;
  backend.durable[1] = encode_schedule(newer);
  assert(!restore_schedule(reboot, backend, fingerprint, 3));
  newer.revision = old.revision + 0x80000000U;
  backend.durable[1] = encode_schedule(newer);
  assert(!restore_schedule(reboot, backend, fingerprint, 3));
  // A separate context's backend/state is unaffected by invalid edits.
  Backend independent; ScheduleContextState other; stage(other);
  assert(apply_schedule(other, independent, fingerprint + 1, 1) == APPLIED);
  assert(other.configured && independent.writes == 1);
  ScheduleSnapshot unused;
  assert(decode_schedule(independent.durable[0], fingerprint + 1, 1, unused));
  assert(!evaluate_schedule(unused.roles[1], false, 100).valid);
  static_assert(sizeof(ScheduleContextState) * 2 + sizeof(ScheduleRecord) * 2 +
      sizeof(ScheduleSnapshot) * 2 <= 1024, "Explicit schedule record budget exceeded");
  if (argc == 2) {
    std::ofstream output(argv[1], std::ios::binary);
    output.write(reinterpret_cast<const char *>(first.data()), first.size());
  }
  std::cout << "PASS transactional schedule storage, recovery and record corruption cases\n";
}
