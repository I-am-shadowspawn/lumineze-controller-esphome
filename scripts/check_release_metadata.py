"""Reject project, manifest, changelog and advertised-profile drift."""
import json
from pathlib import Path
import re
import yaml
ROOT=Path(__file__).resolve().parents[1]

def check(project, release, profiles, changelog):
    assert release['project_name']==project['name'],'release namespace differs from project truth'
    assert release['project_version']==project['version'],'release version differs from project truth'
    assert re.search(r'^## '+re.escape(project['version'])+r'\b',changelog,re.M),'changelog version heading missing'
    assert set(release['profiles'])==set(profiles),'release profile coverage differs from CI manifest'
    assert len(release['profiles'])==4,'four generic profiles required'
    if release['support_status']=='unverified-candidate':
        assert release['source_sha'] is None and release['stable_tag'] is None,'unverified candidate cannot publish a source/tag'
        assert all(v=='pending' for v in release['hardware_gates'].values()),'candidate gate states conflict'
    else:
        assert release['support_status']=='verified' and all(v=='passed' for v in release['hardware_gates'].values()),'stable support requires physical gates'
        assert re.fullmatch('[0-9a-f]{40}',release['source_sha']) and release['stable_tag'],'verified release identity incomplete'
    print('PASS candidate version, profile coverage and gate consistency')

if __name__=='__main__':
    project=yaml.load((ROOT/'packages/core/project.yaml').read_text(),Loader=yaml.BaseLoader)['esphome']['project']
    release=json.loads((ROOT/'release/candidate.json').read_text())
    profiles=json.loads((ROOT/'ci/profile-matrix.json').read_text())['profiles']
    check(project,release,profiles,(ROOT/'CHANGELOG.md').read_text())
