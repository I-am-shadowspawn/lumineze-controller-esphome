#pragma once

#include <algorithm>
#include <cstdint>

#include "fixture_logic.h"

namespace lumineze_topology {

inline void accept_target(FixtureState &fixture, int target, Source source,
                          uint32_t decision_revision, bool in_flight,
                          bool simulated = false) {
  const bool same_in_flight = in_flight && fixture.in_flight == target &&
      fixture.in_flight_source == source &&
      fixture.in_flight_generation == fixture.generation;
  if (!same_in_flight) {
    fixture.attempts = 0;
    fixture.consecutive_failures = 0;
    fixture.retry_delay_ms = 0;
    fixture.generation++;
  }
  fixture.target = target;
  fixture.source = source;
  fixture.target_simulated = source == AUTOMATIC && simulated;
  fixture.decision_revision = decision_revision;
  fixture.pending = true;
  if (source == AUTOMATIC) {
    fixture.automatic_queued = true;
    fixture.last_automatic = target;
  }
}

inline void revoke_pending(FixtureState &fixture) {
  if (fixture.pending) {
    fixture.generation++;
    fixture.pending = false;
  }
}

inline void begin_transaction(FixtureState &fixture, DispatchState &dispatcher,
                              int slot, uint32_t now) {
  dispatcher.active = true;
  dispatcher.active_slot = slot;
  dispatcher.token++;
  dispatcher.started_ms = now;
  dispatcher.write_completed = false;
  dispatcher.failed = false;
  dispatcher.cleanup_pending = false;
  fixture.connected = false;
  fixture.readback_received = false;
  fixture.readback_fresh = false;
  fixture.in_flight = fixture.target;
  fixture.in_flight_source = fixture.source;
  fixture.in_flight_generation = fixture.generation;
  fixture.attempts++;
  fixture.ever_attempted = true;
  fixture.last_attempt_ms = now;
  dispatcher.ever_attempted = true;
  dispatcher.last_attempt_ms = now;
}

inline bool complete_transaction(FixtureState &fixture,
                                 DispatchState &dispatcher, int slot,
                                 uint32_t token) {
  if (!owns_transaction(dispatcher, slot, token)) return false;
  fixture.completed = fixture.in_flight;
  fixture.completed_count++;
  fixture.consecutive_failures = 0;
  fixture.retry_delay_ms = 0;
  fixture.readback_fresh = fixture.readback_received;
  if (fixture.in_flight_generation == fixture.generation) {
    fixture.pending = false;
    fixture.attempts = 0;
  }
  dispatcher.active = false;
  dispatcher.active_slot = -1;
  dispatcher.write_completed = false;
  dispatcher.failed = false;
  dispatcher.cleanup_pending = false;
  dispatcher.next_slot = (slot + 1) % 4;
  return true;
}

enum FailureResult : uint8_t {
  STALE_EVENT,
  NEWER_PENDING,
  RETRY_PENDING,
  TERMINAL_FAILURE,
  CANCELLED_FAILURE,
};

inline FailureResult fail_transaction(FixtureState &fixture,
                                      DispatchState &dispatcher, int slot,
                                      uint32_t token, uint32_t now,
                                      int maximum_attempts,
                                      uint32_t base_delay_ms) {
  if (!owns_transaction(dispatcher, slot, token)) return STALE_EVENT;
  const bool newer = fixture.in_flight_generation != fixture.generation;
  fixture.failure_count++;
  fixture.last_failure_ms = now;
  fixture.readback_fresh = false;
  FailureResult result = CANCELLED_FAILURE;
  if (newer && fixture.pending) {
    fixture.attempts = 0;
    fixture.consecutive_failures = 0;
    fixture.retry_delay_ms = 0;
    result = NEWER_PENDING;
  } else if (!newer) {
    fixture.consecutive_failures++;
    const int shift = std::min(std::max(0, fixture.attempts - 1), 5);
    fixture.retry_delay_ms = static_cast<uint32_t>(
        std::min<uint64_t>(static_cast<uint64_t>(base_delay_ms) << shift,
                           900000ULL));
    if (fixture.attempts >= maximum_attempts) {
      fixture.pending = false;
      result = TERMINAL_FAILURE;
    } else {
      fixture.pending = true;
      result = RETRY_PENDING;
    }
  }
  dispatcher.active = false;
  dispatcher.active_slot = -1;
  dispatcher.write_completed = false;
  dispatcher.failed = false;
  dispatcher.cleanup_pending = false;
  dispatcher.next_slot = (slot + 1) % 4;
  return result;
}

}  // namespace lumineze_topology
