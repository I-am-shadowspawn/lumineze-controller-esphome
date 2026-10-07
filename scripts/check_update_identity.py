"""Verify metadata adds observation only and generic controls reset safely."""
import json
from pathlib import Path
import subprocess
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'ci/profile-matrix.json').read_text())
for profile,entry in manifest['profiles'].items():
    result=subprocess.run([*(sys.argv[1:] or ['esphome']),'config',entry['fixture']],cwd=ROOT,capture_output=True,text=True,check=True)
    config=yaml.load(result.stdout,Loader=yaml.BaseLoader)
    assert 'on_update' not in config['esphome']['project'],profile+' metadata has update action'
    sensors={item.get('id'):item for item in config['text_sensor']}
    for identity in ('controller_project_version','controller_build_profile','controller_esphome_version','controller_source_revision'):
        item=sensors[identity]
        assert not any(name in item for name in ('on_value','on_press','set_action')),identity+' metadata has action'
    switches={item.get('id'):item for item in config['switch']}
    for group in config['lumineze_topology']['groups']:
        for suffix in ('automatic','manual'):
            name=group['id']+'_'+suffix
            assert switches[name]['restore_mode']=='ALWAYS_OFF',profile+': '+name+' may restore on'
    for fixture in config['lumineze_topology']['fixtures']:
        if fixture.get('enabled','true')=='false':continue
        name=fixture['id']+'_manual'
        assert switches[name]['restore_mode']=='ALWAYS_OFF',profile+': '+name+' may restore on'
    print('PASS read-only metadata and boot-off controls '+profile)
