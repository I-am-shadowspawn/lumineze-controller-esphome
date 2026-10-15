"""Assert engine/provider/capability isolation from compiled source."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    'seasonal-production': ('lumineze-generic-ci', 'seasonal', False),
    'seasonal-development': ('lumineze-generic-development-ci', 'seasonal', True),
    'schedule-production': ('lumineze-schedule-ci', 'schedule', False),
    'schedule-development': ('lumineze-schedule-dev-ci', 'schedule', True),
}

def check(name, source, engine, development):
    present = ['evaluate_topology', 'apply_topology_policy', 'dispatcher_tick',
               'evaluate_' + engine + '_contexts',
               'capture_topology_' + ('development' if development else 'real') + '_snapshot']
    absent = ['evaluate_' + ('schedule' if engine == 'seasonal' else 'seasonal') + '_contexts',
              'capture_topology_' + ('real' if development else 'development') + '_snapshot']
    if engine == 'schedule':
        present += ['topology_schedule_contexts', 'schedule_masks']
        absent += ['topology_seasonal_settings', 'seasonal_types.h', 'shared_latitude',
                   'fixture_a_apply_daily_maximum', 'fixture_a_start_fixed_level',
                   'fixture_a_temporary_status']
    else:
        present += ['topology_seasonal_settings', 'fixture_a_apply_daily_maximum']
        absent += ['topology_schedule_contexts', 'schedule_preferences.h', 'shared_apply_schedule']
    if development:
        present += ['topology_simulation_enabled', 'topology_simulated_output_enable']
    else:
        absent += ['topology_simulation_enabled', 'topology_simulated_output_enable',
                   'topology_simulation_time', 'fixture_a_automatic_preview']
    for symbol in present:
        if symbol not in source: raise AssertionError(f'{name}: missing {symbol}')
    for symbol in absent:
        if symbol in source: raise AssertionError(f'{name}: forbidden {symbol}')
    print('PASS compiled isolation ' + name)

if __name__ == '__main__':
    selected = sys.argv[1:] or list(PROFILES)
    for name in selected:
        directory, engine, development = PROFILES[name]
        check(name, (ROOT / 'ci/.esphome/build' / directory / 'src/main.cpp').read_text(), engine, development)
