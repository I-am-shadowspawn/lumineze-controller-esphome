"""Prove lightweight CI path decisions for documentation and firmware edits."""
from ci_change_scope import code_changed
assert not code_changed(['README.md','todo.md','docs/plans/t11-schedule-engine.md','LICENSE'])
assert code_changed(['docs/plans/t11-schedule-engine.md','packages/schedule-production.yaml'])
assert code_changed(['.github/workflows/esphome.yml'])
assert code_changed(['scripts/check_schedule_policy.py'])
assert not code_changed([])
print('PASS docs-only skips heavy jobs; workflow/firmware/test changes require full gates')

# Exercise the actual event reader and final workflow gate in a disposable repo.
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml
ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    directory = Path(tmp)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=directory, text=True).strip()
    git('init', '-q'); git('config', 'user.name', 'CI Scope Test'); git('config', 'user.email', 'ci@example.invalid')
    (directory / 'firmware.yaml').write_text('initial')
    (directory / 'README.md').write_text('initial')
    git('add', '.'); git('commit', '-qm', 'baseline'); before = git('rev-parse', 'HEAD')
    for file, expected in [('README.md', 'false'), ('firmware.yaml', 'true')]:
        (directory / file).write_text('changed')
        git('add', '.'); git('commit', '-qm', 'test change'); head = git('rev-parse', 'HEAD')
        event = directory / 'event.json'; output = directory / 'output.txt'
        event.write_text(json.dumps({'before': before})); output.write_text('')
        env = dict(os.environ, GITHUB_EVENT_PATH=str(event), GITHUB_EVENT_NAME='push', GITHUB_SHA=head, GITHUB_OUTPUT=str(output))
        subprocess.run([sys.executable, str(ROOT / 'scripts/ci_change_scope.py')], cwd=directory, env=env, check=True)
        assert output.read_text() == 'code=' + expected + '\nbaseline=' + before + '\n'
        before = head
workflow = yaml.load((ROOT / '.github/workflows/esphome.yml').read_text(), Loader=yaml.BaseLoader)
gate = workflow['jobs']['required']['steps'][0]['run']
for code, scope, validate, profiles, remote, expected in [
    ('false', 'success', 'skipped', 'skipped', 'skipped', 0),
    ('true', 'success', 'success', 'success', 'success', 0),
    ('true', 'success', 'success', 'failure', 'success', 1),
    ('false', 'failure', 'skipped', 'skipped', 'skipped', 1),
]:
    env = dict(os.environ, CODE=code, SCOPE=scope, VALIDATE=validate, PROFILES=profiles, REMOTE=remote)
    result = subprocess.run(['bash', '-ec', gate], env=env, capture_output=True)
    assert (result.returncode == 0) == (expected == 0)
print('PASS actual Git event decisions and required gate success/failure paths')

from ci_documentation_baseline import outcome, require_baseline
pending = {'id': 1, 'name': 'Required validation', 'app': {'slug': 'github-actions'}, 'status': 'in_progress', 'conclusion': None}
passed = dict(pending, status='completed', conclusion='success')
failed = dict(pending, status='completed', conclusion='failure')
assert outcome([passed]) is True and outcome([failed]) is False and outcome([pending]) is None
require_baseline(lambda: [passed], delay=lambda _: None)
for checks in ([failed], [pending], []):
    try: require_baseline(lambda: checks, delay=lambda _: None, attempts=2)
    except RuntimeError: pass
    else: raise AssertionError('docs-only gate accepted failed/pending/missing source baseline')
print('PASS docs-only inherits passed source checks and rejects failed/pending/missing baseline')
