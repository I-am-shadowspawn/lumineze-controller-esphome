"""Execute T10's independent numeric/validation vectors against the pure helper.

Control and persistence scenarios are exercised by their owning harnesses;
parsing their descriptions is not a behavioral pass.
"""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def scalar(value):
    if isinstance(value, dict):
        method = 'quiet_NaN' if value['non_finite'] == 'nan' else 'infinity'
        return f'std::numeric_limits<float>::{method}()'
    return f'{float(value)}f'


def draft(case, fixtures):
    config = {**fixtures.get(case.get('fixture'), {}), **case}
    statements = [f'input.mode = schedule_mode("{config.get("mode", "linear")}");']
    points = config.get('points', [])
    statements.append(f'input.count = {len(points)};')
    for point in points[:8]:
        index = point['slot'] - 1
        statements.append(f'input.points[{index}] = {{{str(point["enabled"]).lower()}, '
                          f'{scalar(point["minute"])}, {scalar(point["level"])}}};')
    return '\n'.join(statements)


def main():
    data = json.loads((ROOT / 'tests/data/schedule-cases.json').read_text())
    source = ['#include <cassert>', '#include <limits>',
              '#include "components/lumineze_topology/schedule_logic.h"',
              '#include "components/lumineze_topology/fixture_logic.h"',
              'using namespace lumineze_topology;', 'int main() {']
    for case in data['evaluations']:
        source += ['{ ScheduleInput input;', draft(case, data['fixtures']),
                   'ScheduleRole active;',
                   'assert(validate_schedule(input, true, active) == SCHEDULE_OK);',
                   f'auto r = evaluate_schedule(active, true, {scalar(case["minute"])});',
                   f'assert(r.valid && std::abs(r.percent - {scalar(case["expected_percent"])}) '
                   f'<= {scalar(data["expected_percent_tolerance"])});', '}']
    errors = {'capacity':'BAD_CAPACITY', 'mode':'BAD_MODE',
              'minute_range':'BAD_MINUTE', 'integer_minute':'BAD_MINUTE',
              'finite_minute':'BAD_MINUTE', 'level_range':'BAD_LEVEL',
              'integer_level':'BAD_LEVEL', 'finite_level':'BAD_LEVEL',
              'duplicate_enabled_minute':'DUPLICATE_MINUTE',
              'used_role_requires_two_points':'TOO_FEW_POINTS'}
    for case in data['validations']:
        if case.get('reason') == 'role':
            source.append(f'assert(schedule_role("{case["role"]}") == -1);')
            continue
        source += ['{ ScheduleInput input;', draft(case, data['fixtures']),
                   'ScheduleRole active; active.points[0].level = 37;']
        used = str(case.get('used', True)).lower()
        if case.get('reason') in errors:
            source += [f'assert(validate_schedule(input, {used}, active) == '
                       f'{errors[case["reason"]]});',
                       'assert(active.points[0].level == 37);']
        else:
            source.append(f'assert(validate_schedule(input, {used}, active) == SCHEDULE_OK);')
            snapshot = case.get('snapshot')
            if snapshot:
                source.append(f'assert(!evaluate_schedule(active, true, {scalar(snapshot["minute"])}, '
                              f'{str(snapshot["valid"]).lower()}).valid);')
            elif case['expected'] == 'accept_invalid_output':
                source.append('assert(!evaluate_schedule(active, false, 0).valid);')
        source.append('}')
    for case in data['fixture_conversions']:
        src = {'fixture_manual':'FIXTURE_MANUAL', 'group_manual':'GROUP_MANUAL'}.get(
            case.get('source'), 'AUTOMATIC')
        demand = scalar(case.get('percent', 0) / 100)
        source += ['{ ConversionInput input{' +
                   f'{src}, {scalar(case["maximum"])}, {demand}, 1.0f, {demand}, '
                   f'{case.get("requested", 0)}, 0, 2, false, false, false, false, true' + '};',
                   'auto result = convert_fixture(input);',
                   f'assert(result.valid && result.target == {case["expected_target"]});', '}']
    source.append('}')
    with tempfile.TemporaryDirectory() as directory:
        cpp = Path(directory) / 'schedule.cpp'
        binary = Path(directory) / 'schedule'
        cpp.write_text('\n'.join(source))
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-I', str(ROOT), str(cpp), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print('PASS schedule helper: 56 output, 22 validation and 8 conversion cases')
    print('Policy/HA and persistence scenarios remain owned by later T11 increments')


if __name__ == '__main__':
    main()
