"""Bounded profile compile retries, retained logs and reviewed static budgets."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import yaml
from check_ci_artifacts import check_config
ROOT=Path(__file__).resolve().parents[1]

def sizes(log):
    result={}
    for field,marker in [('ram_bytes','RAM:'),('flash_bytes','Flash:')]:
        matches=re.findall(re.escape(marker)+r'.*?used ([\d,]+) bytes',log)
        if not matches: raise AssertionError('missing compiler size '+field)
        result[field]=int(matches[-1].replace(',',''))
    return result

def budget(result, limits):
    for field in ('ram_bytes','flash_bytes'):
        assert result[field] <= limits[field],f'{field} {result[field]} exceeds budget {limits[field]}'

def compile_retry(command, directory, attempts=3, delay=time.sleep):
    directory.mkdir(parents=True,exist_ok=True)
    for attempt in range(1,attempts+1):
        print(f'Compile attempt {attempt}/{attempts}',flush=True)
        process=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        output=process.stdout+process.stderr
        (directory/f'compile-attempt-{attempt}.log').write_text(output)
        print('\n'.join(output.splitlines()[-30:]),flush=True)
        if process.returncode==0: return output
        if attempt<attempts: delay(attempt*20)
    raise RuntimeError(f'compilation failed after {attempts} attempts (exit {process.returncode})')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('profile')
    parser.add_argument('--esphome',default='esphome')
    parser.add_argument('--artifacts',type=Path,default=ROOT/'ci/artifacts')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'ci/profile-matrix.json').read_text())
    entry=manifest['profiles'][args.profile]
    resolved=subprocess.run([args.esphome,'config',entry['fixture']],cwd=ROOT,capture_output=True,text=True,check=True)
    check_config(yaml.load(resolved.stdout,Loader=yaml.BaseLoader))
    directory=args.artifacts/args.profile
    log=compile_retry([args.esphome,'compile',entry['fixture']],directory)
    result=sizes(log); budget(result,manifest['static_budgets'])
    result.update(profile=args.profile,toolchain=manifest['toolchain'],
                  warning_lines=[line for line in log.splitlines() if 'warning:' in line.lower()],
                  source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  hardware_verified=False)
    (directory/'build-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    subprocess.run([sys.executable,str(ROOT/'scripts/check_profile_isolation.py'),args.profile],check=True)
    print('PASS profile build and static budgets '+args.profile)

if __name__=='__main__':main()
