"""Always report a CI decision; documentation-only updates skip heavy jobs."""
import json
import os
from pathlib import Path
import subprocess

def code_changed(paths):
    return any(not (path.endswith('.md') or path.startswith('docs/') or path=='LICENSE') for path in paths)

def paths_for_event(event, kind):
    head=os.environ.get('GITHUB_SHA','HEAD')
    base=event.get('before')
    if kind=='pull_request':
        head=event['pull_request']['head']['sha']
        base=event.get('before') if event.get('action')=='synchronize' else None
        base=base or event['pull_request']['base']['sha']
    if kind in ('workflow_dispatch','merge_group'):return ['packages/forced-check.yaml']
    if not base or set(base)=={'0'}:
        return subprocess.check_output(['git','ls-files'],text=True).splitlines()
    exists=subprocess.run(['git','cat-file','-e',base+'^{commit}'],capture_output=True).returncode==0
    if not exists:return ['packages/conservative-full-check.yaml']
    return subprocess.check_output(['git','diff','--name-only',base,head],text=True).splitlines()

if __name__=='__main__':
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    changed=code_changed(paths_for_event(event,os.environ['GITHUB_EVENT_NAME']))
    print('Full software validation required' if changed else 'Documentation-only update: heavy validation skipped')
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('code='+str(changed).lower()+'\n')
