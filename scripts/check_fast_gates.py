"""Run the declared checkout-only regressions with named failure output."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'ci/profile-matrix.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
    binary=str(Path(tmp)/'fixtures')
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'tests/test_fixture_logic.cpp'),'-o',binary],check=True)
    subprocess.run([binary],check=True)
for name in manifest['fast_checks']:
    print('GATE '+name,flush=True)
    result=subprocess.run([sys.executable,str(ROOT/'scripts'/name)],capture_output=True,text=True)
    print(result.stdout,end='')
    if result.returncode:
        print(result.stderr,file=sys.stderr,end='')
        raise SystemExit('FAILED '+name)
    if name=='check_schedule_policy.py':
        cases=json.loads((ROOT/'tests/data/schedule-cases.json').read_text())['transitions']
        expected={c['id'] for c in cases}
        passed={line.removeprefix('PASS ') for line in result.stdout.splitlines() if line.startswith('PASS ')}
        assert expected <= passed,'schedule transition corpus lacks executable coverage: '+str(expected-passed)
print('PASS all declared software gates')
