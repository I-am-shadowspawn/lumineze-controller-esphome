"""Prove manifest and generated-source isolation gates reject injected drift."""
import copy
import json
from pathlib import Path
import sys
from check_profile_manifest import check as check_manifest
from check_profile_isolation import PROFILES, check as check_source
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'ci/profile-matrix.json').read_text())
mutant=copy.deepcopy(manifest); mutant['profiles'].pop('schedule-development')
try:
    check_manifest(mutant,(ROOT/'.github/workflows/esphome.yml').read_text())
except AssertionError as e:
    assert 'four profile entries' in str(e)
else:
    raise AssertionError('manifest gate accepted a missing profile')
print('PASS manifest gate rejects omitted profile')
for name in sys.argv[1:] or ['schedule-production']:
    directory, engine, development=PROFILES[name]
    source=(ROOT/'ci/.esphome/build'/directory/'src/main.cpp').read_text()
    check_source(name,source,engine,development)
    symbol='topology_seasonal_settings' if engine=='schedule' else 'topology_schedule_contexts'
    try:
        check_source(name,source+'\n'+symbol,engine,development)
    except AssertionError as e:
        assert 'forbidden '+symbol in str(e)
    else:
        raise AssertionError('source isolation gate accepted cross-engine state')
    print('PASS '+name+' rejects injected cross-engine state')
