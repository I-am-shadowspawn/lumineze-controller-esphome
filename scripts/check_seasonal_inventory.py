"""Compare seasonal entity/settings contracts with the compatibility baseline."""
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
METADATA_IDS = {'controller_project_version', 'controller_build_profile', 'controller_esphome_version', 'controller_source_revision'}
FIELDS = ('id', 'name', 'platform', 'internal', 'entity_category',
          'disabled_by_default', 'restore_value', 'restore_mode', 'initial_value',
          'min_value', 'max_value', 'step', 'unit_of_measurement')
KINDS = ('number', 'switch', 'button', 'sensor', 'binary_sensor', 'text_sensor')
PROFILES = {'production': 'ci/topology-generic.yaml',
            'development': 'ci/topology-generic-development.yaml'}


def resolved_entities(entries):
    for item in entries:
        # Platforms such as debug put their entities inside a platform entry.
        if 'id' not in item and 'name' not in item:
            children = [dict(child, platform=item['platform']) for child in item.values()
                        if isinstance(child, dict) and ('id' in child or 'name' in child)]
            if children:
                yield from children
                continue
        yield item


def inventory(text):
    config = yaml.load(text, Loader=yaml.BaseLoader)
    return {kind: sorted(({key: item[key] for key in FIELDS if key in item}
                         for item in resolved_entities(config.get(kind, []))
                         if item.get('id') not in METADATA_IDS),
                        key=lambda item: ('id' not in item, item.get('id', item.get('name', ''))))
            for kind in KINDS}


def main():
    baseline = json.loads((ROOT / 'tests/data/seasonal-profile-baseline.json').read_text())
    command = sys.argv[1:] or ['esphome']
    for name, path in PROFILES.items():
        result = subprocess.run([*command, 'config', path], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        actual = inventory(result.stdout)
        if actual != baseline['profiles'][name]:
            raise AssertionError(f'{name} entity/settings contract changed; review baseline migration')
        print(f'PASS {name} entity identities, defaults and restore contract match compatibility baseline')


if __name__ == '__main__':
    main()
