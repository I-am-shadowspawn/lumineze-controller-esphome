"""Docs-only success requires the preceding source commit's verified gates."""
import json
import os
import re
import time
from urllib.request import Request, urlopen

def outcome(checks):
    matching=[c for c in checks if c['name']=='Required validation' and c.get('app',{}).get('slug')=='github-actions']
    if not matching:return None
    latest=max(matching,key=lambda c:c['id'])
    if latest['status']!='completed':return None
    return latest['conclusion']=='success'

def require_baseline(fetch, delay=time.sleep, attempts=90):
    for attempt in range(attempts):
        result=outcome(fetch())
        if result is True:return
        if result is False:raise RuntimeError('preceding source validation failed; docs-only update cannot override it')
        if attempt+1<attempts:delay(20)
    raise RuntimeError('preceding source validation still pending/missing; rerun the lightweight gate after completion')

if __name__=='__main__':
    revision=os.environ['BASELINE_SHA'];assert re.fullmatch('[0-9a-f]{40}',revision),'missing immutable baseline SHA'
    repository=os.environ['GITHUB_REPOSITORY'];assert re.fullmatch(r'[\w.-]+/[\w.-]+',repository)
    def fetch():
        request=Request(f'https://api.github.com/repos/{repository}/commits/{revision}/check-runs?check_name=Required%20validation&per_page=100',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
        with urlopen(request,timeout=30) as response:return json.load(response)['check_runs']
    require_baseline(fetch)
    print('PASS docs-only update inherits successful preceding-source validation')
