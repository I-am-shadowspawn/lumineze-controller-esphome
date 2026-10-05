#pragma once

#include <cstdint>
#include <array>

namespace lumineze_topology {

enum Source : uint8_t {
  HOLD = 0,
  AUTOMATIC = 1,
  GROUP_MANUAL = 2,
  FIXTURE_MANUAL = 3,
  SAFETY = 4,
  TEMPORARY_FIXED = 5,
};

enum TemporaryMode : uint8_t { TEMPORARY_NONE, DAILY_MAXIMUM, TIMED_FIXED_LEVEL };
enum TemporaryStatus : uint8_t {
  TEMP_STATUS_INACTIVE,
  TEMP_STATUS_ARMED,
  TEMP_STATUS_HOLDING,
  TEMP_STATUS_ENFORCING,
  TEMP_STATUS_FIXED,
  TEMP_STATUS_RETURNING,
  TEMP_STATUS_REJECTED,
};

// The external component defines storage types and immutable bindings only.
// The seasonal engine, policy and transaction sequencing live in YAML packages.
struct ContextState {
  float latitude = -28.5f;
  float noon_minutes = 750.0f;
  float phase_days = 182.6f;
  float visible_winter = 0.75f;
  float visible_summer = 1.0f;
  float visible_exponent = 1.0f;
  float uv_start_minutes = 90.0f;
  float uv_end_minutes = 90.0f;
  float uv_winter = 0.8f;
  float uv_summer = 1.0f;
  float uv_exponent = 1.0f;
  float desired[2] = {0.0f, 0.0f};
  float peak[2] = {0.0f, 0.0f};
  float curve[2] = {0.0f, 0.0f};
  bool valid = false;
  bool simulated = false;
  bool simulated_output_enabled = false;
  uint32_t revision = 0;
};

struct EvaluationSnapshot {
  int year = 0;
  int day_of_year = 0;
  int days_in_year = 365;
  float minutes = 0.0f;
  bool valid = false;
  bool simulated = false;
  bool simulated_output_enabled = false;
};

struct GroupState {
  bool automatic = false;
  bool manual = false;
  float manual_fraction = 0.0f;
  Source source = HOLD;
  float demand = 0.0f;
  bool valid = false;
  uint32_t revision = 0;
  uint32_t context_revision = 0;
};

struct FixtureState {
  float maximum = 0.0f;
  bool calibration_ready = false;
  float last_maximum = 0.0f;
  int minimum_change = 2;
  bool manual = false;
  int manual_level = 0;
  int target = 0;
  Source source = HOLD;
  bool target_simulated = false;
  uint32_t decision_revision = 0;
  bool pending = false;
  uint32_t generation = 0;
  int in_flight = 0;
  Source in_flight_source = HOLD;
  uint32_t in_flight_generation = 0;
  int completed = -1;
  int reported = -1;
  bool readback_received = false;
  bool readback_fresh = false;
  bool connected = false;
  bool ever_attempted = false;
  uint32_t last_attempt_ms = 0;
  uint32_t last_failure_ms = 0;
  uint32_t retry_delay_ms = 0;
  int attempts = 0;
  int consecutive_failures = 0;
  uint32_t completed_count = 0;
  uint32_t failure_count = 0;
  bool automatic_queued = false;
  int last_automatic = -1;
  bool invalid_output = false;
  bool limit_applied = false;
  bool failsafe_sent = false;
  TemporaryMode temporary_mode = TEMPORARY_NONE;
  TemporaryStatus temporary_status = TEMP_STATUS_INACTIVE;
  uint8_t temporary_rejection = 0;
  bool temporary_force_reevaluation = false;
  int temporary_maximum = 0;
  bool temporary_maximum_crossed = false;
  int temporary_fixed_level = 0;
  int temporary_year = 0;
  int temporary_day = 0;
  uint32_t temporary_started_ms = 0;
  uint32_t temporary_duration_ms = 0;
};

struct DispatchState {
  bool active = false;
  int active_slot = -1;
  uint32_t token = 0;
  uint32_t started_ms = 0;
  bool write_completed = false;
  bool failed = false;
  bool cleanup_pending = false;
  uint32_t cleanup_started_ms = 0;
  bool ever_attempted = false;
  uint32_t last_attempt_ms = 0;
  int next_slot = 0;
};

}  // namespace lumineze_topology
