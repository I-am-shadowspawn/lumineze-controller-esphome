"""Reject missing advertised profile coverage and checkout/manifest drift."""
import json
from pathlib import Path
import re
from check_topology_matrix import CASES
ROOT=Path(__file__).resolve().parents[1]

def check(manifest, workflow):
    profiles=manifest['profiles']
    expected={e+'-'+p for e in ('seasonal','schedule') for p in ('production','development')}
    assert set(profiles)==expected,'four profile entries required'
    pin=(ROOT/'requirements-ci.txt').read_text().strip().split('==')[1]
    assert manifest['toolchain']['esphome']==pin,'toolchain pin mismatch'
    matrix=re.search(r'profile: \[([^\]]+)\]',workflow)
    assert matrix and {s.strip() for s in matrix[1].split(',')}==expected,'full-build job matrix mismatch'
    assert {c['id'] for c in manifest['topology_cases']}=={c[0] for c in CASES},'topology case coverage mismatch'
    for name,p in profiles.items():
        assert p['engine']==name.split('-')[0] and p['provider']==('development' if name.endswith('development') else 'real'),name
        assert (ROOT/p['fixture']).is_file(),name+' fixture missing'
        assert p['temporary_lighting']==(p['engine']=='seasonal'),name+' capability mismatch'
        assert p['simulation_entities']==(p['provider']=='development'),name+' provider capability mismatch'
        assert 'full-compile' in p['checks'],name+' full-build coverage missing'
    for script in manifest['fast_checks']:
        assert (ROOT/'scripts'/script).is_file(),script
    print('PASS complete profile/CI coverage manifest')

if __name__=='__main__':
    check(json.loads((ROOT/'ci/profile-matrix.json').read_text()),(ROOT/'.github/workflows/esphome.yml').read_text())
