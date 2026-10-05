"""Build ordinary Git-package consumers from an empty directory at one SHA."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import yaml
from build_profile import compile_retry
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/I-am-shadowspawn/lumineze-controller-esphome'

def compose(profile, revision):
    assert re.fullmatch('[0-9a-f]{40}',revision),'consumer requires immutable 40-character SHA'
    engine,flavour=profile.split('-');development=flavour=='development'
    files=[f'packages/{profile}.yaml',{'path':f'packages/topology/context-{engine}.yaml','vars':{'context_id':'vivarium','context_name':'Vivarium'}}]
    if engine=='schedule':
        files += [{'path':'packages/topology/context-schedule-role.yaml','vars':{'context_id':'vivarium','schedule_role':role}} for role in ('visible','uv')]
    files += [{'path':'packages/topology/group.yaml','vars':{'group_id':role,'group_name':'Vivarium '+role.title()}} for role in ('visible','uv')]
    fixture='fixture-luminize-schedule.yaml' if engine=='schedule' else 'fixture-luminize.yaml'
    fixtures=[{'id':'uv_lamp','slot':0,'type':'prot5','group':'uv','mac':'AA:BB:CC:DD:EE:02'}, {'id':'visible_lamp','slot':3,'type':'jungle_dawn','group':'visible','mac':'AA:BB:CC:DD:EE:01'}]
    for f in fixtures:
        files.append({'path':'packages/topology/'+fixture,'vars':{'fixture_id':f['id'],'fixture_name':f['id'].replace('_',' ').title(),'fixture_mac':f['mac'],'fixture_default_maximum':0 if f['type']=='prot5' else 100}})
        if development:
            files.append({'path':'packages/topology/fixture-luminize-development.yaml','vars':{'fixture_id':f['id'],'fixture_name':f['id'].replace('_',' ').title()}})
    return {'substitutions':{'device_name':'remote-'+profile,'friendly_name':'Remote CI','timezone':'Europe/London'},
            'packages':{'controller':{'url':URL,'ref':revision,'files':files}},
            'external_components':[{'source':{'type':'git','url':URL,'ref':revision},'components':['lumineze_topology']}],
            'lumineze_topology':{'topology_version':1,'engine_family':engine,'input_provider':'development' if development else 'real','contexts':[{'id':'vivarium'}],
                                'groups':[{'id':role,'context':'vivarium','output':role} for role in ('visible','uv')],'fixtures':fixtures},
            'wifi':{'ssid':'ci-network','password':'ci-password'}}

def same_revision(config, revision):
    assert config['packages']['controller']['ref']==revision and all(entry['source'].get('ref')==revision for entry in config['external_components']),'package/helper candidate revisions differ'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ref',required=True);parser.add_argument('--profile',default='schedule-production');parser.add_argument('--all',action='store_true');parser.add_argument('--compile',action='store_true');parser.add_argument('--esphome',default='esphome');args=parser.parse_args()
    profiles=list(json.loads((ROOT/'ci/profile-matrix.json').read_text())['profiles']) if args.all else [args.profile]
    for profile in profiles:
        config=compose(profile,args.ref);same_revision(config,args.ref)
        # A wrong helper revision is rejected independently of network availability.
        config['external_components'][0]['source']['ref']='0'*40
        try: same_revision(config,args.ref)
        except AssertionError: pass
        else: raise AssertionError('wrong helper ref accepted')
        config['external_components'][0]['source'].pop('ref')
        try: same_revision(config,args.ref)
        except AssertionError: pass
        else: raise AssertionError('missing helper ref accepted')
        config['external_components'][0]['source']['ref']=args.ref
        with tempfile.TemporaryDirectory(prefix='lumineze-consumer-') as tmp:
            directory=Path(tmp);path=directory/'controller.yaml';path.write_text(yaml.safe_dump(config,sort_keys=False))
            assert not (directory/'components').exists() and not (directory/'packages').exists()
            for action in ('config','compile') if args.compile else ('config',):
                if action == 'compile':
                    compile_retry([args.esphome,action,str(path)],directory/'logs',cwd=directory)
                else:
                    result=subprocess.run([args.esphome,action,str(path)],cwd=directory,capture_output=True,text=True)
                    if result.returncode: raise RuntimeError(f'{profile} remote {action} failed: '+(result.stdout+result.stderr)[-3000:])
                print(f'PASS remote {profile} {action} at {args.ref}',flush=True)
