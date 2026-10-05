#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>

#include "../components/lumineze_topology/transport_logic.h"

using namespace lumineze_topology;

int main() {
  FixtureState temporary;
  assert(apply_daily_maximum(temporary, 60, 2026, 100));
  assert(temporary.temporary_mode == DAILY_MAXIMUM &&
         temporary.temporary_status == TEMP_STATUS_ARMED);
  auto daily = apply_daily_maximum_to_target(temporary, 65, true, false);
  assert(daily.holding && !daily.force_submit && daily.target == 60);
  daily = apply_daily_maximum_to_target(temporary, 80, true, true);
  assert(daily.holding && daily.force_submit && daily.target == 60 &&
         temporary.temporary_status == TEMP_STATUS_ENFORCING);
  temporary.target = 60;
  daily = apply_daily_maximum_to_target(temporary, 59, false, false);
  assert(daily.released && daily.force_submit && daily.target == 59 &&
         temporary.temporary_mode == TEMPORARY_NONE);
  assert(apply_daily_maximum(temporary, 60, 2026, 100));
  assert(expire_temporary(temporary, true, false, 2026, 101, 1000));
  assert(temporary.temporary_mode == TEMPORARY_NONE);
  FixtureState armed_correction;
  assert(apply_daily_maximum(armed_correction, 60, 2026, 100));
  armed_correction.target = 80;
  daily = apply_daily_maximum_to_target(armed_correction, 50, false, true);
  assert(!daily.holding && daily.force_submit && daily.target == 50 &&
         armed_correction.temporary_mode == DAILY_MAXIMUM &&
         !armed_correction.temporary_maximum_crossed);
  armed_correction.temporary_status = TEMP_STATUS_ARMED;  // confirmed by policy
  daily = apply_daily_maximum_to_target(armed_correction, 50, false, false);
  assert(!daily.released && !daily.holding &&
         armed_correction.temporary_status == TEMP_STATUS_ARMED);
  daily = apply_daily_maximum_to_target(armed_correction, 65, true, false);
  assert(daily.holding && !daily.force_submit && daily.target == 60 &&
         armed_correction.temporary_maximum_crossed);
  assert(start_timed_fixed_level(temporary, 35, 7200000U, UINT32_MAX - 1000U));
  assert(temporary.temporary_mode == TIMED_FIXED_LEVEL);
  assert(!expire_temporary(temporary, true, false, 2026, 101, 1000U));
  assert(expire_temporary(temporary, true, false, 2026, 101, 7199000U));
  assert(!start_timed_fixed_level(temporary, 35, 1000U, 0));
  assert(start_timed_fixed_level(temporary, 100, 900000U, 0));
  ConversionInput fixed_input{TEMPORARY_FIXED, 80.0f, 0.0f, 0.0f, 0.0f,
                              100, 0, 2, false, false, false, false, true};
  const auto fixed_result = convert_fixture(fixed_input);
  assert(fixed_result.valid && fixed_result.submit && fixed_result.target == 80 &&
         fixed_result.limit_applied);

  for (int quarter = 1; quarter <= 96; ++quarter)
    assert(valid_fixed_duration_hours(quarter / 4.0f));
  for (float hours : {0.0f, 0.24f, 0.3f, 1.1f, 24.25f,
                     std::numeric_limits<float>::infinity(),
                     std::numeric_limits<float>::quiet_NaN()})
    assert(!valid_fixed_duration_hours(hours));
  const auto valid_generation = temporary.generation;
  assert(!start_timed_fixed_level(temporary, 35, 1080000U, 0));
  assert(temporary.generation == valid_generation &&
         temporary.temporary_mode == TIMED_FIXED_LEVEL);

  // Release follows historical exceedance, independent of diagnostic status.
  FixtureState crossed;
  assert(apply_daily_maximum(crossed, 60, 2026, 100));
  crossed.target = 60;
  daily = apply_daily_maximum_to_target(crossed, 60, false, false);
  assert(!daily.released && crossed.temporary_mode == DAILY_MAXIMUM);
  apply_daily_maximum_to_target(crossed, 61, false, false);
  crossed.temporary_status = TEMP_STATUS_ARMED;
  daily = apply_daily_maximum_to_target(crossed, 60, false, false);
  assert(daily.released && !daily.force_submit);

  // A same-level restart is a new authorization, even during an old write.
  FixtureState restarted;
  DispatchState restart_dispatch;
  assert(start_timed_fixed_level(restarted, 35, 900000U, 100));
  accept_target(restarted, 35, TEMPORARY_FIXED, 1, false);
  begin_transaction(restarted, restart_dispatch, 0, 200);
  const auto old_generation = restarted.generation;
  restarted.readback_received = true;
  assert(start_timed_fixed_level(restarted, 35, 1800000U, 300));
  assert(restarted.generation != old_generation && !restarted.pending &&
         !restarted.readback_received && !restarted.readback_fresh);
  accept_target(restarted, 35, TEMPORARY_FIXED, 2, true);
  restarted.readback_received = true;  // late old readback cannot confirm restart
  assert(complete_transaction(restarted, restart_dispatch, 0,
                              restart_dispatch.token));
  assert(restarted.target == 35 && restarted.pending &&
         restarted.completed == 35 && !restarted.readback_fresh);
  begin_transaction(restarted, restart_dispatch, 0, 400);
  restarted.reported = 35;
  restarted.readback_received = true;
  assert(complete_transaction(restarted, restart_dispatch, 0,
                              restart_dispatch.token));
  assert(!restarted.pending && restarted.readback_fresh);

  // Unsolicited/obsolete readback remains a report, never fresh confirmation.
  record_readback(restarted, restart_dispatch, 0, 80);
  assert(restarted.reported == 80 && !restarted.readback_fresh &&
         !restarted.readback_received);
  accept_target(restarted, 35, TEMPORARY_FIXED, 3, false);
  begin_transaction(restarted, restart_dispatch, 0, 450);
  record_readback(restarted, restart_dispatch, 0, 35);
  assert(!restarted.readback_received);  // response before readback window
  restart_dispatch.write_completed = true;
  record_readback(restarted, restart_dispatch, 1, 35);
  assert(!restarted.readback_received);  // wrong slot
  record_readback(restarted, restart_dispatch, 0, 20);
  assert(restarted.readback_received);  // valid response, mismatched level
  assert(complete_transaction(restarted, restart_dispatch, 0,
                              restart_dispatch.token));
  assert(restarted.readback_fresh && restarted.reported != restarted.completed);

  // Replacing fixed with daily revokes its retries; old completion is physical
  // history only. Cancellation also revokes an in-flight-only generation.
  assert(start_timed_fixed_level(restarted, 80, 900000U, 500));
  accept_target(restarted, 80, TEMPORARY_FIXED, 3, false);
  begin_transaction(restarted, restart_dispatch, 0, 600);
  assert(apply_daily_maximum(restarted, 60, 2026, 100));
  accept_target(restarted, 60, AUTOMATIC, 4, true);
  restarted.readback_received = true;
  assert(complete_transaction(restarted, restart_dispatch, 0,
                              restart_dispatch.token));
  assert(restarted.target == 60 && restarted.completed == 80 &&
         restarted.pending && !restarted.readback_fresh);
  begin_transaction(restarted, restart_dispatch, 0, 700);
  restarted.pending = false;
  cancel_temporary(restarted);
  assert(fail_transaction(restarted, restart_dispatch, 0,
                          restart_dispatch.token, 800, 3, 30000) == CANCELLED_FAILURE);
  assert(!restarted.pending && !restarted.readback_fresh);

  assert(resolve_source(true, true, GROUP_MANUAL) == SAFETY);
  assert(resolve_source(false, true, GROUP_MANUAL) == FIXTURE_MANUAL);
  assert(resolve_source(false, false, GROUP_MANUAL) == GROUP_MANUAL);
  assert(resolve_source(false, false, AUTOMATIC) == AUTOMATIC);
  assert(resolve_source(false, false, HOLD) == HOLD);
  ConversionInput input{AUTOMATIC, 100.0f, 0.72f, 0.72f, 1.0f,
                        0, 0, 2, false, false, false, false, true};
  auto result = convert_fixture(input);
  assert(result.valid && result.submit && result.target == 72);
  input.maximum = 60.0f;
  result = convert_fixture(input);
  assert(result.valid && result.target == 43);
  input.source = GROUP_MANUAL;
  result = convert_fixture(input);
  assert(result.valid && result.target == 43);
  input.source = FIXTURE_MANUAL;
  input.manual_level = 80;
  result = convert_fixture(input);
  assert(result.valid && result.target == 60 && result.limit_applied);

  input.maximum = std::numeric_limits<float>::quiet_NaN();
  assert(!convert_fixture(input).valid);
  input.source = SAFETY;
  result = convert_fixture(input);
  assert(result.valid && result.target == 0);
  input.source = AUTOMATIC;
  input.demand = 0.0f;
  input.peak = 0.0f;
  input.curve = 0.0f;
  assert(convert_fixture(input).valid);
  input.demand = std::numeric_limits<float>::infinity();
  assert(!convert_fixture(input).valid);

  input = {AUTOMATIC, 98.0f, 0.5f, 1.0f, 0.5f,
           0, 50, 2, true, true, false, false, false};
  result = convert_fixture(input);
  assert(result.valid && result.target == 49 && result.submit);
  input.cap_reduced = false;
  assert(!convert_fixture(input).submit);
  input.previous_invalid = true;
  assert(convert_fixture(input).submit);
  input = {AUTOMATIC, 60.0f, 1.0f, 1.0f, 1.0f,
           0, 60, 2, true, false, false, false, false};
  assert(!convert_fixture(input).submit);
  input.source_changed = true;
  assert(convert_fixture(input).submit);

  const bool enabled[4] = {true, false, false, true};
  const bool due[4] = {true, true, true, true};
  assert(select_due_slot(1, enabled, due) == 3);
  assert(select_due_slot(0, enabled, due) == 0);
  const bool none[4] = {false, false, false, false};
  assert(select_due_slot(0, enabled, none) == -1);
  assert(elapsed(10U, UINT32_MAX - 5U, 16U));
  assert(!elapsed(10U, UINT32_MAX - 5U, 17U));
  DispatchState dispatcher;
  dispatcher.active = true;
  dispatcher.active_slot = 3;
  dispatcher.token = 42;
  assert(owns_transaction(dispatcher, 3, 42));
  assert(!owns_transaction(dispatcher, 3, 41));
  assert(!owns_transaction(dispatcher, 0, 42));

  FixtureState fixture;
  DispatchState arbiter;
  accept_target(fixture, 40, AUTOMATIC, 1, false);
  begin_transaction(fixture, arbiter, 3, 100);
  const auto first_token = arbiter.token;
  accept_target(fixture, 60, AUTOMATIC, 2, true);
  assert(complete_transaction(fixture, arbiter, 3, first_token));
  assert(fixture.completed == 40 && fixture.target == 60 && fixture.pending);
  begin_transaction(fixture, arbiter, 3, 200);
  const auto second_token = arbiter.token;
  assert(!complete_transaction(fixture, arbiter, 3, first_token));
  assert(arbiter.active && arbiter.token == second_token);
  assert(complete_transaction(fixture, arbiter, 3, second_token));
  assert(fixture.completed == 60 && !fixture.pending);

  accept_target(fixture, 20, FIXTURE_MANUAL, 3, false);
  begin_transaction(fixture, arbiter, 3, 300);
  revoke_pending(fixture);
  assert(complete_transaction(fixture, arbiter, 3, arbiter.token));
  assert(!fixture.pending);
  fixture.reported = 70;
  accept_target(fixture, 25, AUTOMATIC, 4, false);
  begin_transaction(fixture, arbiter, 3, 400);
  assert(fail_transaction(fixture, arbiter, 3, arbiter.token,
                          500, 2, 30000) == RETRY_PENDING);
  assert(fixture.pending && fixture.reported == 70);
  begin_transaction(fixture, arbiter, 3, 600);
  assert(fail_transaction(fixture, arbiter, 3, arbiter.token,
                          700, 2, 30000) == TERMINAL_FAILURE);
  assert(!fixture.pending && fixture.reported == 70);
  accept_target(fixture, 30, AUTOMATIC, 5, false);
  begin_transaction(fixture, arbiter, 3, 800);
  accept_target(fixture, 20, GROUP_MANUAL, 6, true);
  assert(fail_transaction(fixture, arbiter, 3, arbiter.token,
                          900, 2, 30000) == NEWER_PENDING);
  assert(fixture.pending && fixture.target == 20 && fixture.attempts == 0);

  GroupState group;
  group.source = AUTOMATIC;
  group.valid = true;
  update_group_demand(group, 0.5f, true);
  const auto accepted_revision = group.revision;
  group.source = HOLD;
  group.valid = false;
  update_group_demand(group, 0.0f, false);
  update_group_demand(group, 0.5f, true);
  assert(group.revision == accepted_revision);
  update_group_demand(group, 0.6f, true);
  assert(group.revision == accepted_revision + 1);
  assert(!automatic_output_allowed(true, false));
  assert(automatic_output_allowed(true, true));
  assert(automatic_output_allowed(false, false));
  assert(!invalid_real_clock(false, true));
  assert(invalid_real_clock(false, false));
  assert(!invalid_real_clock(true, false));
  assert(automatic_refresh_required(true, false));
  assert(!automatic_refresh_required(true, true));
  assert(!automatic_refresh_required(false, false));

  FixtureState reevaluated;
  DispatchState reevaluation_dispatch;
  accept_target(reevaluated, 50, AUTOMATIC, 1, false);
  begin_transaction(reevaluated, reevaluation_dispatch, 0, 1000);
  const ConversionInput unchanged_input{
      AUTOMATIC, 100.0f, 0.5f, 0.5f, 1.0f, 0, reevaluated.target, 2,
      reevaluated.automatic_queued, false, false, false, false};
  for (int evaluation = 0; evaluation < 2; ++evaluation) {
    const auto unchanged = convert_fixture(unchanged_input);
    assert(unchanged.valid && !unchanged.submit);
    assert(reevaluated.attempts == 1);
    assert(reevaluated.in_flight_generation == reevaluated.generation);
  }
  const auto completed_token = reevaluation_dispatch.token;
  assert(complete_transaction(reevaluated, reevaluation_dispatch, 0,
                              completed_token));
  assert(reevaluated.completed_count == 1 && reevaluated.attempts == 0);

  FixtureState coalesced;
  DispatchState coalesced_dispatch;
  accept_target(coalesced, 50, AUTOMATIC, 1, false);
  begin_transaction(coalesced, coalesced_dispatch, 0, 2000);
  accept_target(coalesced, 60, AUTOMATIC, 2, true);
  accept_target(coalesced, 70, AUTOMATIC, 3, true);
  assert(fail_transaction(coalesced, coalesced_dispatch, 0,
                          coalesced_dispatch.token, 2100, 3, 30000) ==
         NEWER_PENDING);
  assert(coalesced.target == 70 && coalesced.pending &&
         coalesced.attempts == 0);

  FixtureState simulated_target;
  accept_target(simulated_target, 50, AUTOMATIC, 1, false, true);
  const ConversionInput live_recalculation{
      AUTOMATIC, 100.0f, 0.51f, 0.8f, 0.6375f, 0, simulated_target.target,
      2, true, false, false, false,
      automatic_refresh_required(simulated_target.target_simulated, false)};
  const auto live_decision = convert_fixture(live_recalculation);
  assert(live_decision.valid && live_decision.submit);
  accept_target(simulated_target, live_decision.target, AUTOMATIC, 2, false,
                false);
  assert(!simulated_target.target_simulated);
}
