#!/usr/bin/env python3
"""Offline validation of the README, config, workflows, and all SVG assets."""
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from build_profile import ROOT

errors=[]
def check(value,msg):
    if not value: errors.append(msg)

cfg=json.loads((ROOT/'config/profile.json').read_text())
readme=(ROOT/'README.md').read_text(encoding='utf-8')
check(cfg['username']=='orionstar65','This package targets username orionstar65; update validator when repurposing')
check(cfg['greeting']=='Hello, I am Senior Software Engineer','Anonymous greeting does not match approved text')
check('YOUR NAME' not in readme, 'Unexpected name placeholder in README')
check('orionstar65' in readme,'Target GitHub link missing')
check('AWAITING FIRST SYNC' not in readme and 'BUILD  •  SHIP' not in readme,'Temporary portfolio copy present')
check(readme.count('<picture>')==10,'Expected 10 picture elements: hero, about, stack, 4 projects, metrics, snake, footer')
# README contains hero/terminal/stack, four projects, metrics/snake, footer = 10
matches=re.findall(r'(?:src|srcset)="(\./assets/[^\"]+)"',readme)
for asset in matches:
    check((ROOT/asset.removeprefix('./')).is_file(),f'Referenced image missing: {asset}')

for path in (ROOT/'assets').rglob('*.svg'):
    try:
        tree=ET.parse(path)
        check(tree.getroot().tag=='{http://www.w3.org/2000/svg}svg',f'Not an SVG root: {path}')
        data=path.read_text(encoding='utf-8').lower()
        check('<script' not in data and '<foreignobject' not in data,f'Unsafe element: {path}')
        # Local fragment references are safe and sometimes used by animated SVG tools.
        for element in tree.iter():
            for k,v in element.attrib.items():
                if k.endswith('href'):
                    check(v.startswith('#'),f'External SVG reference: {path} -> {v}')
    except ET.ParseError as exc: errors.append(f'SVG XML invalid: {path}: {exc}')

for filename in ['update-metrics.yml','contribution-snake.yml','validate-readme.yml']:
    check((ROOT/'.github/workflows'/filename).exists(),f'Workflow missing: {filename}')
if errors:
    for issue in errors:print('FAIL:',issue)
    sys.exit(1)
print(f'OK: README, {len(matches)} local image refs, {len(list((ROOT/"assets").rglob("*.svg")))} SVGs, and workflow files.')
