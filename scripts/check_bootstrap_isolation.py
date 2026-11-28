"""Verify the bootstrap firmware cannot operate lamps and carries a safe CI boundary.

Checks the resolved ``ci/bootstrap.yaml`` configuration:
- lamp transport absent: no ``ble_client``, no ``lumineze_topology`` section,
  no external components,
- identity intact: project name and bootstrap build profile,
- provisioning surfaces present: captive portal, Improv Serial,
- commissioning begins disarmed and is excluded from restore,
- CI boundary inputs are dummies: fixture Wi-Fi and setup AP passwords must be
  the CI placeholders, never the published production default.

ESPHome renders values that match a registered secret as ``!secret <name>``;
placeholder names are mapped back through ``ci/secrets.yaml`` before asserting.
"""
import re
import subprocess
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def clean(value):
    return re.sub(r'(?:\x1b|\\033)\[\d+m', '', str(value))


def main():
    esphome = sys.argv[1:] or ['esphome']
    base = yaml.load((ROOT / 'ci/secrets.yaml').read_text(), Loader=yaml.BaseLoader)
    result = subprocess.run([*esphome, 'config', 'ci/bootstrap.yaml'],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    raw = yaml.load(result.stdout, Loader=yaml.BaseLoader)

    def resolve(value):
        name = clean(value)
        return base.get(name, name)

    config = raw
    # No BLE clients means no lamp transport.
    assert not config.get('ble_client'), 'bootstrap must not declare BLE clients'
    # No operational topology engine.
    topo = config.get('lumineze_topology', {})
    assert not topo.get('operational'), 'bootstrap must not set topology operational'
    assert not topo.get('fixtures'), 'bootstrap must not declare fixtures'
    assert 'lumineze_topology' not in config, 'bootstrap must not enable the topology component'
    assert not config.get('external_components'), 'bootstrap must not need helper components'
    # Project identity must label bootstrap.
    assert config['esphome']['project']['name'] == 'shadowspawn.lumineze'
    assert config['esphome']['min_version'] == '2026.11.0'
    sensors = {s['id']: s for s in config.get('text_sensor', [])}
    assert sensors['controller_build_profile']['lambda'] == 'return {"bootstrap"};'
    assert 'Bootstrap' in sensors['controller_source_revision']['lambda']
    # Provisioning must stay available for the first install.
    assert config.get('captive_portal') is not None, 'bootstrap needs captive portal provisioning'
    assert config.get('improv_serial') is not None, 'bootstrap needs Improv Serial provisioning'
    # Commissioning must start disarmed and not survive a reset armed.
    switches = {s['id']: s for s in config.get('switch', [])}
    assert switches['topology_commissioned']['restore_mode'] == 'RESTORE_DEFAULT_OFF', \
        'commissioning must restore to disarmed'
    assert switches['topology_commissioned']['lambda'] == 'return false;', \
        'bootstrap commissioning must default to disarmed'
    # CI fixture boundary: every credential in the resolved bootstrap build is a dummy.
    wifi = config['wifi']
    networks = wifi.get('networks', [wifi])
    assert networks and all(resolve(n.get('ssid')) == 'ci-network'
                            and resolve(n.get('password')) == 'ci-password'
                            for n in networks), 'CI bootstrap must use dummy Wi-Fi credentials'
    ap = wifi.get('ap', {})
    assert clean(ap.get('ssid', '')).startswith('LuminEZE Bootstrap'), 'unexpected setup AP name'
    assert resolve(ap.get('password')) == 'ci-password', \
        'CI bootstrap must override the published setup AP password with the CI dummy'
    print('PASS bootstrap has no lamp transport and correct identity')
    print('PASS bootstrap CI boundary uses dummy credentials only')


if __name__ == '__main__':
    main()

