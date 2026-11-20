"""Prove retry termination/log retention and budget-failure behavior."""
from pathlib import Path
import sys
import tempfile
from build_profile import budget, compile_retry, sizes
from check_ci_artifacts import check_config
with tempfile.TemporaryDirectory() as tmp:
    directory=Path(tmp)
    command=[sys.executable,'-c','import sys; print("simulated download failure"); sys.exit(23)']
    waits=[]
    try: compile_retry(command,directory,delay=waits.append)
    except RuntimeError as e: assert 'exit 23' in str(e)
    else: raise AssertionError('final failed compile was masked')
    assert waits==[20,40] and len(list(directory.glob('compile-attempt-*.log')))==3
    result=sizes('RAM: [x] (used 100 bytes from 200 bytes)\nFlash: [x] (used 300 bytes from 400 bytes)')
    try: budget(result,{'ram_bytes':99,'flash_bytes':400})
    except AssertionError as e: assert 'ram_bytes' in str(e)
    else: raise AssertionError('over-budget profile accepted')
print('PASS final compile failure propagates, all attempts retained, budget breach rejected')

try:
    check_config({'wifi': {'networks': [{'ssid': 'ci-network', 'password': 'private-value'}]}})
except AssertionError as e:
    assert 'non-dummy Wi-Fi' in str(e)
else:
    raise AssertionError('private credential input accepted')
print('PASS private credential input rejected before retained build logging')
