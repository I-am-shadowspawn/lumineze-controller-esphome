"""Restrict CI build inputs to dummy credentials and retained artifact types."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import yaml
ROOT=Path(__file__).resolve().parents[1]

def clean(value):
    return re.sub(r'(?:\x1b|\\033)\[\d+m','',str(value))

def check_config(config):
    wifi=config['wifi']
    networks=wifi.get('networks',[wifi])
    assert networks and all(clean(n.get('ssid'))=='ci-network' and clean(n.get('password'))=='ci-password' for n in networks),'CI fixture has non-dummy Wi-Fi credentials'
    assert not wifi.get('ap'),'CI artifact input must not contain private fallback credentials'
    assert not config.get('api',{}).get('encryption'),'CI artifact input must not contain an API key'
    assert all(not entry.get('password') for entry in config.get('ota',[])),'CI artifact input must not contain OTA credentials'
    for client in config.get('ble_client',[]):
        assert clean(client['mac_address']).upper().startswith('AA:BB:CC:DD:EE:'),'CI fixture has non-dummy lamp address'

def check_artifacts(directory):
    for file in directory.rglob('*'):
        if not file.is_file():continue
        assert file.name=='build-summary.json' or re.fullmatch(r'compile-attempt-[1-3]\.log',file.name),'unexpected retained artifact type'
        text=file.read_text()
        for mac in re.findall(r'(?i)(?:[0-9a-f]{2}:){5}[0-9a-f]{2}',text):
            assert mac.upper().startswith('AA:BB:CC:DD:EE:'),'artifact contains non-dummy address'
    print('PASS retained artifact boundary '+str(directory))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('profile');parser.add_argument('--esphome',default='esphome');parser.add_argument('--artifacts',type=Path,default=ROOT/'ci/artifacts');args=parser.parse_args()
    entry=json.loads((ROOT/'ci/profile-matrix.json').read_text())['profiles'][args.profile]
    result=subprocess.run([args.esphome,'config',entry['fixture']],cwd=ROOT,capture_output=True,text=True,check=True)
    check_config(yaml.load(result.stdout,Loader=yaml.BaseLoader))
    check_artifacts(args.artifacts/args.profile)
    print('PASS dummy CI input boundary '+args.profile)
