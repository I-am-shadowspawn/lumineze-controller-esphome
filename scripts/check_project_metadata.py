"""Compare resolved project/profile metadata with shared truth and compiled source."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import yaml
ROOT=Path(__file__).resolve().parents[1]
IDS={'controller_project_version','controller_build_profile','controller_esphome_version','controller_source_revision'}

def verify(config, profile, truth, pin):
    assert config['esphome']['project']==truth,'project namespace/version differs from shared truth'
    assert config['esphome']['min_version']==pin,'unsupported minimum version claim'
    sensors={s['id']:s for s in config['text_sensor']}
    assert IDS<=set(sensors),'identity diagnostics incomplete'
    assert sensors['controller_build_profile']['lambda']==f'return {{"{profile}"}};','profile metadata mismatch'
    assert sensors['controller_project_version']['lambda']=='return {ESPHOME_PROJECT_VERSION};'
    assert sensors['controller_esphome_version']['platform']=='version' and sensors['controller_esphome_version']['hide_timestamp']=='true'
    assert all(sensors[i]['entity_category']=='diagnostic' for i in IDS)
    for kind in ('number','select','switch','button'):
        assert not IDS & {s.get('id') for s in config.get(kind,[])},'runtime identity is editable'
    source=sensors['controller_source_revision']['lambda']
    assert ('Unverified legacy reference' in source) if profile.startswith('legacy') else source=='return {lumineze_topology::build_source_revision};'
    print('PASS resolved identity '+profile)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--esphome',default='esphome');parser.add_argument('--profile');parser.add_argument('--compiled',action='store_true');parser.add_argument('--require-clean',action='store_true');args=parser.parse_args()
    manifest=json.loads((ROOT/'ci/profile-matrix.json').read_text())
    profiles=dict(manifest['profiles'])
    profiles.update({'legacy-seasonal-production':{'fixture':'ci/controller.yaml'},'legacy-seasonal-development':{'fixture':'ci/controller-development.yaml'}})
    truth=yaml.load((ROOT/'packages/core/project.yaml').read_text(),Loader=yaml.BaseLoader)['esphome']['project']
    for profile in [args.profile] if args.profile else profiles:
        result=subprocess.run([args.esphome,'config',profiles[profile]['fixture']],cwd=ROOT,capture_output=True,text=True,check=True)
        config=yaml.load(result.stdout,Loader=yaml.BaseLoader)
        verify(config,profile,truth,manifest['toolchain']['esphome'])
        if args.compiled:
            entry=profiles[profile];directory=ROOT/'ci/.esphome/build'/entry['build_directory']/'src'
            source=(directory/'main.cpp').read_text();defines=(directory/'esphome/core/defines.h').read_text()
            for field,macro in [('name','ESPHOME_PROJECT_NAME'),('version','ESPHOME_PROJECT_VERSION')]:
                assert f'#define {macro} "{truth[field]}"' in defines,'compiled project metadata mismatch'
            assert f'return {{"{profile}"}};' in source,'compiled profile mismatch'
            revision=re.search(r'build_source_revision = "([^"]+)"',source)
            assert revision and re.fullmatch('[0-9a-f]{40}(?:\\+dirty)?',revision[1]),'missing resolved source SHA'
            if args.require_clean:
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
                assert revision[1]==head,'compiled source is not current clean candidate'
            print('PASS compiled identity '+profile)
