"""Prove named software gates reject faults in disposable checkout copies."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    copy=Path(tmp)
    for directory in ('scripts','components','packages','tests'):
        shutil.copytree(ROOT/directory,copy/directory,ignore=shutil.ignore_patterns('__pycache__'))
    cases=copy/'tests/data/schedule-cases.json'
    original=cases.read_text(); data=json.loads(original)
    case=next(c for c in data['evaluations'] if 'expected_percent' in c)
    case['expected_percent'] += 10
    cases.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,str(copy/'scripts/check_schedule_cases.py')],capture_output=True,text=True)
    assert result.returncode!=0 and 'Assertion' in result.stderr,'schedule oracle failed to detect injected expected-output fault'
    cases.write_text(original)
    print('PASS check_schedule_cases rejects injected output fault')
    transport=copy/'components/lumineze_topology/transport_logic.h'
    original=transport.read_text()
    target='if (fixture.in_flight_generation == fixture.generation) {'
    assert original.count(target)==1
    transport.write_text(original.replace(target,'if (true) {'))
    result=subprocess.run([sys.executable,str(copy/'scripts/check_schedule_policy.py')],capture_output=True,text=True)
    assert result.returncode!=0 and 'Assertion' in result.stderr,'production policy failed to detect stale completion fault'
    print('PASS check_schedule_policy rejects injected stale-generation fault')
print('PASS injected faults stayed outside working checkout')
