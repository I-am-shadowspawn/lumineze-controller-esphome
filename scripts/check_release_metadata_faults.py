"""Prove release drift and premature stable support are rejected."""
import copy
import json
from pathlib import Path
import yaml
from check_release_metadata import check
ROOT=Path(__file__).resolve().parents[1]
project=yaml.load((ROOT/'packages/core/project.yaml').read_text(),Loader=yaml.BaseLoader)['esphome']['project']
release=json.loads((ROOT/'release/candidate.json').read_text())
profiles=json.loads((ROOT/'ci/profile-matrix.json').read_text())['profiles']
changelog=(ROOT/'CHANGELOG.md').read_text()
for title,mutation in (
    ('version mismatch', lambda r:r.update(project_version='9.9.9')),
    ('profile omitted', lambda r:r['profiles'].remove('schedule-development')),
    ('premature stable label', lambda r:r.update(support_status='verified', stable_tag='v2.0.0',source_sha='0'*40)),
):
    variant=copy.deepcopy(release);mutation(variant)
    try:check(project,variant,profiles,changelog)
    except AssertionError:print('PASS rejected '+title)
    else:raise AssertionError('accepted '+title)
