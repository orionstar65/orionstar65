#!/usr/bin/env python3
"""Render accurate public GitHub metrics (no scraped counters, no made-up data).

Run via GitHub Actions. Use --placeholder only when initializing a new profile
before the first successful remote sync.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
import sys

from build_profile import ROOT, THEMES, svg, backdrop, rect, circle, text, line, MONO


def fetch_json(url):
    headers={
        'Accept':'application/vnd.github+json',
        'User-Agent':'cybernetic-engineering-profile/1.0',
        'X-GitHub-Api-Version':'2022-11-28',
    }
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
        return json.load(response)


def github_metrics(username):
    api='https://api.github.com'
    account=fetch_json(f'{api}/users/{username}')
    results=[]
    for page in range(1,22):
        chunk=fetch_json(f'{api}/users/{username}/repos?per_page=100&page={page}&sort=updated&type=owner')
        if not isinstance(chunk,list):raise RuntimeError('Unexpected GitHub API result')
        results.extend(r for r in chunk if not r.get('private',False))
        if len(chunk)<100:break
    else:
        raise RuntimeError('Repo count exceeded pagination safety limit; increase limit')
    recent_cutoff=datetime.now(timezone.utc)-timedelta(days=90)
    recent=0
    for repo in results:
        pushed=repo.get('pushed_at')
        if pushed and datetime.fromisoformat(pushed.replace('Z','+00:00'))>=recent_cutoff:recent+=1
    return [
        ('PUBLIC REPOS',account['public_repos']),
        ('STARS RECEIVED',sum(r.get('stargazers_count',0) for r in results)),
        ('FOLLOWERS',account['followers']),
        ('PUSHED IN 90D',recent),
    ]


def render(metrics,mode,updated=None):
    W,H=1280,260;t=THEMES[mode]; ident='metr'+mode
    p=[backdrop(W,H,t,ident),text(34,56,'04   /   GITHUB INTELLIGENCE',18,t['cyan'],700,MONO,spacing=1.2),
       text(35,88,'Public account snapshot',27,t['text'],800)]
    boxw=287
    for i,(label,value) in enumerate(metrics):
        x=29+i*314
        p += [rect(x,108,boxw,117,14,t['surface'],t['border']),
              line(x+17,129,x+67,129,t['cyan'] if i%2==0 else t['purple'],2.3,.8),
              text(x+18,181,str(value),38,t['text'],800),
              text(x+18,207,label,13,t['muted'],700,MONO,spacing=.8)]
    if updated:
        p.append(text(34,247,'SOURCE: GitHub REST API  ·  UPDATED '+updated,12,t['muted'],600,MONO))
    else:
        p.append(text(34,247,'PUBLIC GITHUB ACTIVITY',12,t['muted'],600,MONO))
    return svg(W,H,''.join(p),t,ident)


def snake_placeholder(mode):
    W,H=1280,196;t=THEMES[mode]; ident='snk'+mode
    p=[backdrop(W,H,t,ident),text(34,53,'CONTRIBUTION CURRENT',17,t['cyan'],700,MONO,spacing=1.1)]
    # Decorative cells, explicitly NOT a contribution graph or activity estimate.
    for row in range(5):
        for col in range(43):
            x=34+col*18;y=74+row*18
            p.append(rect(x,y,11,11,3,t['chip'],t['border'],.65))
    p += [rect(856,63,380,101,16,t['surface'],t['border']),
          circle(881,90,5,t['purple'],extra='class="blink"'),
          text(899,95,'PUBLIC CONTRIBUTIONS',17,t['text'],700,MONO),
          text(879,126,'GitHub activity visualization',15,t['sub']),
          text(879,148,'',15,t['sub'])]
    return svg(W,H,''.join(p),t,ident)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--placeholder',action='store_true');args=ap.parse_args()
    cfg=json.loads((ROOT/'config/profile.json').read_text())
    out=ROOT/'assets/generated';out.mkdir(parents=True,exist_ok=True)
    if args.placeholder:
        for mode in THEMES:
            metricfile=out/f'metrics-{mode}.svg'
            snakefile=out/f'snake-{mode}.svg'
            if not metricfile.exists():metricfile.write_text(render([(k,'—') for k in ['PUBLIC REPOS','STARS RECEIVED','FOLLOWERS','PUSHED IN 90D']],mode),encoding='utf-8')
            if not snakefile.exists():snakefile.write_text(snake_placeholder(mode),encoding='utf-8')
        print('Placeholders created without simulated activity data.');return
    try:
        metrics=github_metrics(cfg['username'])
    except (urllib.error.URLError,ValueError,KeyError,RuntimeError) as exc:
        sys.exit(f'GitHub API request failed; existing artifacts preserved. Error: {exc}')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    for mode in THEMES:
        (out/f'metrics-{mode}.svg').write_text(render(metrics,mode,stamp),encoding='utf-8')
    print('Updated public metrics:',metrics,'at',stamp)

if __name__=='__main__':main()
