#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>

#include "../components/lumineze_topology/transport_logic.h"

using namespace lumineze_topology;

int main() {
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
}
