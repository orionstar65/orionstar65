#!/usr/bin/env python3
"""Build all editable profile SVGs + README with Python standard library only.

Metrics and snake are deliberately *not* overwritten here: those are produced
by their own workflows. The committed placeholders make first render safe.
"""
import argparse
import html
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/profile.json'

THEMES = {
    'dark': {
        'bg':'#081226', 'bg2':'#111F37', 'surface':'#10213B', 'border':'#294363',
        'text':'#F4F8FF', 'sub':'#A5BEDD', 'muted':'#7090AE', 'grid':'#14304E',
        'cyan':'#39D7F4', 'purple':'#AC83FF', 'chip':'#132A47', 'halo':'#0B3656',
        'code':'#10233C', 'bright':'#D6F8FF'
    },
    'light': {
        'bg':'#F4F9FF', 'bg2':'#E9F2FC', 'surface':'#FFFFFF', 'border':'#C4D9E9',
        'text':'#10213B', 'sub':'#37526F', 'muted':'#607F98', 'grid':'#DAE7F3',
        'cyan':'#007BAA', 'purple':'#7351C7', 'chip':'#E7F3FA', 'halo':'#DAF0FC',
        'code':'#EAF3FB', 'bright':'#005D82'
    }
}

FONTS = 'Arial,Helvetica,sans-serif'
MONO = 'Consolas,Menlo,monospace'

def e(x): return html.escape(str(x), quote=True)

def text(x,y,s,size=20,color=None,weight=400,font=None,opacity=None,spacing=None,anchor=None):
    props = f'x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color or "currentColor"}" font-family="{font or FONTS}"'
    if opacity is not None: props += f' opacity="{opacity}"'
    if spacing: props += f' letter-spacing="{spacing}"'
    if anchor: props += f' text-anchor="{anchor}"'
    return f'<text {props}>{e(s)}</text>'

def rect(x,y,w,h,r,fill,stroke=None,sw=1, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+ (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') +f' {extra}/>'

def line(x1,y1,x2,y2,color,width=1,opacity=1,extra=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" opacity="{opacity}" {extra}/>'

def circle(x,y,r,fill,stroke=None,sw=1,opacity=1,extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+f' opacity="{opacity}" {extra}/>'

def svg(w,h,inner,t,ident):
    defs = f'''<defs>
       <linearGradient id="wash-{ident}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['bg']}"/><stop offset="1" stop-color="{t['bg2']}"/></linearGradient>
       <linearGradient id="edge-{ident}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['cyan']}"/><stop offset="0.55" stop-color="{t['purple']}"/><stop offset="1" stop-color="{t['cyan']}"/></linearGradient>
       <radialGradient id="glow-{ident}"><stop offset="0" stop-color="{t['cyan']}" stop-opacity=".21"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></radialGradient>
       <clipPath id="clip-{ident}"><rect width="{w}" height="{h}" rx="24"/></clipPath>
       </defs>'''
    style='''<style>
    @keyframes beacon {0%,100%{opacity:.45} 50%{opacity:1}}
    @keyframes orbit {from{transform:rotate(0deg)} to{transform:rotate(360deg)}}
    @keyframes scan {from{transform:translateX(-110%)} to{transform:translateX(225%)}}
    .blink{animation:beacon 2.6s ease-in-out infinite}
    .orbit{transform-box:fill-box;transform-origin:center;animation:orbit 32s linear infinite}
    .scan{animation:scan 12s ease-in-out infinite}
    @media (prefers-reduced-motion:reduce){.blink,.orbit,.scan{animation:none!important}}
    </style>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Cybernetic Engineering portfolio art">{defs}{style}<g clip-path="url(#clip-{ident})">{inner}</g></svg>\n'

def backdrop(w,h,t,ident):
    p=[rect(0,0,w,h,24,f'url(#wash-{ident})'),rect(0,0,w,h,24,'none',t['border'],1.5),
       circle(int(w*.78),int(h*.40),int(h*.90),f'url(#glow-{ident})')]
    for x in range(24,w,40):p.append(line(x,0,x,h,t['grid'],.8,.48))
    for y in range(22,h,40):p.append(line(0,y,w,y,t['grid'],.8,.48))
    p += [line(28,14,135,14,t['cyan'],2.3,.9),line(w-129,h-15,w-27,h-15,t['purple'],2.4,.65)]
    return ''.join(p)

def icon_mark(x,y,size,t):
    # Hexagon, route lines, central architecture symbol: hand-drawn, not a borrowed logo.
    r=size/2; pts=[]
    for n in range(6):
        a=math.pi/3*n-math.pi/6;pts.append(f'{x+math.cos(a)*r:.1f},{y+math.sin(a)*r:.1f}')
    nodes=' '.join(pts)
    g=f'<polygon points="{nodes}" fill="{t["chip"]}" stroke="{t["cyan"]}" stroke-width="2.4"/>'
    g+= f'<path d="M{x-12} {y} l9 -9 m-9 9 l9 9 M{x+12} {y} l-9 -9 m9 9 l-9 9" stroke="{t["cyan"]}" fill="none" stroke-width="3.1" stroke-linecap="round"/>'
    return g

def hero(cfg,t,dark):
    W,H=1280,365;ident='hero'+('d' if dark else 'l')
    p=[backdrop(W,H,t,ident)]
    p += [rect(33,31,12,12,6,t['cyan'],extra='class="blink"'),text(55,42,cfg['eyebrow'],15,t['cyan'],700,MONO,spacing=1.5)]
    # The title deliberately has no personal name or filler role badge.
    p += [text(44,103,'Hello, I am',29,t['sub'],700,spacing=.8),
          text(42,169,'Senior Software',55,t['text'],800,spacing=-1.8),
          text(42,232,'Engineer',65,t['text'],800,spacing=-1.8)]
    # The professional headline uses two balanced lines to remain readable
    # within the hero's left text column (rather than colliding with the illustration).
    tagline_parts=[item.strip() for item in cfg['tagline'].split('|') if item.strip()]
    if len(tagline_parts)>=4:
        hero_lines=['  |  '.join(tagline_parts[:2]), '  |  '.join(tagline_parts[2:])]
    elif len(tagline_parts)>=2:
        pivot=(len(tagline_parts)+1)//2
        hero_lines=['  |  '.join(tagline_parts[:pivot]), '  |  '.join(tagline_parts[pivot:])]
    else:
        hero_lines=[cfg['tagline']]
    for i,headline in enumerate(hero_lines[:2]):
        p.append(text(43,278+i*31,headline,20,t['sub'],600))
    p.append(text(43,343,'github.com/'+cfg['username'],15,t['muted'],600,MONO))
    # Orbit / network ring illustration on the right; visual only, no metrics fabricated.
    cx,cy=1035,180
    p += [circle(cx,cy,162,'none',t['border'],1,0.6),circle(cx,cy,119,'none',t['cyan'],1.2,.4),circle(cx,cy,77,'none',t['purple'],1.6,.6)]
    p += [f'<g class="orbit">'+circle(cx,cy,145,'none',t['purple'],1.2,.35,extra='stroke-dasharray="6 18"')+
          circle(cx+145,cy,7,t['cyan'])+circle(cx-145,cy,5,t['purple'])+'</g>']
    for j,(vx,vy) in enumerate([(847,68),(1220,63),(1200,294),(894,287),(1040,13),(1034,348)]):
        p.append(line(cx,cy,vx,vy,t['cyan'] if j%2 else t['purple'],1,.2))
        p.append(circle(vx,vy,3,t['cyan'] if j%2 else t['purple'],opacity=.65))
    p += [icon_mark(cx,cy,103,t),text(cx,298,'[ SYSTEM DESIGN ]',14,t['muted'],600,MONO,anchor='middle')]
    p += [rect(770,297,101,26,8,t['chip'],t['border']),text(782,315,'AI SYSTEMS',12,t['cyan'],700,MONO),
          rect(1140,315,102,26,8,t['chip'],t['border']),text(1150,333,'CLOUD / API',12,t['purple'],700,MONO)]
    return svg(W,H,''.join(p),t,ident)

def terminal(cfg,t,dark):
    W,H=1280,303; ident='termd' if dark else 'terml'
    p=[backdrop(W,H,t,ident)]
    p += [rect(28,28,609,246,18,t['code'],t['border']),rect(28,28,609,39,18,t['surface'])]
    for i,c in enumerate([t['purple'],t['cyan'],t['muted']]):p.append(circle(49+i*19,49,5,c))
    p += [text(113,55,'~/portfolio/profile.ts',14,t['muted'],600,MONO),
          text(58,98,'const engineer = {',20,t['sub'],500,MONO),
          text(82,132,'focus:',20,t['cyan'],500,MONO),text(163,132,'"full-stack + AI",',20,t['text'],500,MONO),
          text(82,165,'mindset:',20,t['cyan'],500,MONO),text(181,165,'"systems thinking",',20,t['text'],500,MONO),
          text(82,198,'default:',20,t['cyan'],500,MONO),text(181,198,'"ship with care"',20,t['text'],500,MONO),
          text(58,231,'};',20,t['sub'],500,MONO),
          text(692,67,'01   /   ENGINEERING PROFILE',18,t['cyan'],700,MONO,spacing=1),
          text(692,116,'End-to-end, by design.',34,t['text'],800),
          text(692,159,'Products, platforms, and the systems',23,t['sub']),
          text(692,190,'that make them dependable.',23,t['sub'])]
    for i,label in enumerate(cfg['principles']):
        xx=693; yy=225+i*22
        p += [circle(xx+4,yy-5,4,t['cyan'] if i%2==0 else t['purple']),text(xx+18,yy,label,16,t['sub'],600)]
    return svg(W,H,''.join(p),t,ident)

def stack(cfg,t,dark):
    W,H=1280,426;ident='stackd' if dark else 'stackl';p=[backdrop(W,H,t,ident)]
    p += [text(35,61,'02    /    TECHNOLOGY ARSENAL',18,t['cyan'],700,MONO,spacing=1.4),
          text(36,101,'The right tools for the right problems.',29,t['text'],800)]
    names=list(cfg['skills'])
    for j,name in enumerate(names):
        x=28+j*314;y=129;w=297
        p += [rect(x,y,w,247,16,t['surface'],t['border']),rect(x+16,y+18,36,36,11,t['chip'],t['border']),
              text(x+34,y+42,['01','02','03','04'][j],16,t['cyan'] if j%2==0 else t['purple'],700,MONO,anchor='middle'),
              text(x+63,y+42,name,22,t['text'],700)]
        for i,skill in enumerate(cfg['skills'][name][:5]):
            yy=y+79+i*32
            p += [circle(x+28,yy-5,3.2,t['cyan'] if j%2==0 else t['purple']),text(x+43,yy,skill,18,t['sub'])]
    p += [text(36,407,'ARCHITECT  /  IMPLEMENT  /  OBSERVE  /  IMPROVE',14,t['muted'],600,MONO,spacing=1)]
    return svg(W,H,''.join(p),t,ident)

def project(pr,t,dark):
    W,H=620,310;ident='pr'+pr['slug']+('d' if dark else 'l');accent=t['cyan'] if pr['accent']=='cyan' else t['purple']
    p=[backdrop(W,H,t,ident)]
    p += [rect(22,23,255,30,10,t['chip'],t['border']),text(35,44,pr['type'],11,accent,700,MONO,spacing=.25),
          text(26,100,pr['title'],32,t['text'],800),text(26,136,pr['subtitle'],16,t['sub']),
          line(26,157,595,157,t['border'],1,1)]
    import textwrap
    lines=textwrap.wrap(pr['details'],width=65,break_long_words=False)
    for i,desc in enumerate(lines[:2]):p.append(text(26,188+i*22,desc,15,t['sub']))
    x=26
    for tag in pr['tags'][:3]:
        ww=min(180,22+len(tag)*9)
        p += [rect(x,245,ww,28,9,t['chip'],t['border']),text(x+10,264,tag,13,accent,700,MONO)]
        x+=ww+9
    p += [circle(560,67,44,'none',accent,1.2,.48),circle(560,67,27,'none',t['border'],1.2,.85),
          f'<path d="M545 67h30 M560 52v30" stroke="{accent}" stroke-width="2" opacity=".8"/>',
          text(25,295,('PUBLIC REPOSITORIES  ↗' if pr['link'] else ('PRIVATE PROJECT' if pr['slug']=='roleward' else 'EXPERIENCE HIGHLIGHT')),12,t['muted'],700,MONO)]
    return svg(W,H,''.join(p),t,ident)

def footer(cfg,t,dark):
    W,H=1280,188;ident='footd' if dark else 'footl';p=[backdrop(W,H,t,ident)]
    p += [text(44,50,'05   /   LET’S CONNECT',17,t['cyan'],700,MONO,spacing=1),
          text(42,111,'LET’S CONNECT.',39,t['text'],800),
          text(44,151,'Full-stack engineering  ·  Data platforms  ·  Applied AI',21,t['sub'])]
    p += [icon_mark(1090,96,116,t),text(1090,175,'@'+cfg['username'],14,t['muted'],600,MONO,anchor='middle')]
    return svg(W,H,''.join(p),t,ident)

def markdown(cfg):
    def pic(folder,file,alt,width='100%'):
        return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="./assets/{folder}/{file}-dark.svg">\n'
                f'  <img src="./assets/{folder}/{file}-light.svg" alt="{e(alt)}" width="{width}">\n</picture>')
    projects=cfg['projects']
    cells=[]
    for pr in projects:
        image=pic('projects',pr['slug'],pr['title']+' — '+pr['subtitle'])
        title=e(pr['title'])
        headline = f'<a href="{e(pr["link"])}"><strong>{title} ↗</strong></a>' if pr['link'] else f'<strong>{title}</strong> <sub>· {"private project" if pr["slug"]=="roleward" else "engineering experience"}</sub>'
        cells.append(f'<td width="50%" valign="top">\n\n{image}\n\n{headline}\n\n{e(pr["details"])}\n\n</td>')
    table='\n'.join(f'<tr>\n{cells[i]}\n{cells[i+1]}\n</tr>' for i in (0,2))
    html_links=['<a href="'+e(cfg['links']['github'])+'">GitHub</a>']
    for label,key in [('Portfolio','portfolio'),('LinkedIn','linkedin'),('Email','email')]:
        url=cfg['links'].get(key,'').strip()
        if url:html_links.append('<a href="'+e(url if key!='email' or url.startswith('mailto:') else 'mailto:'+url)+'">'+label+'</a>')
    focus=' • '.join(cfg['focus'])
    return f'''<!-- GENERATED by scripts/build_profile.py. Edit config/profile.json instead. -->
<div align="center">

{pic('hero','banner',cfg['greeting']+' — Full Stack, Data Platforms, Production LLM and RAG Solutions, Agentic AI Development')}

<br>

<strong>{e(cfg['tagline'])}</strong>

{(' &nbsp;·&nbsp; '.join(html_links))}

</div>

### `01` &nbsp; A little about me

{pic('sections','terminal','Code-inspired introduction and engineering philosophy')}

{e(cfg['intro'])}

- **Currently exploring:** {', '.join(cfg['focus'][:3])}.
- **How I work:** {', '.join(cfg['principles']).rstrip('.')}.
- **What matters:** Clear interfaces, measured trade-offs, maintainable architecture, and dependable delivery.

### `02` &nbsp; Technology arsenal

{pic('sections','stack','Technology areas and stacks')}

<details>
<summary><strong>Expand the full stack as accessible text</strong></summary>

'''+ '\n'.join(f'- **{e(cat)}:** {", ".join(map(e,items))}' for cat,items in cfg['skills'].items()) +f'''

</details>

### `03` &nbsp; Selected work

<table>
{table}
</table>

<sub>Selected work includes private projects and professional experience; public repositories are linked when available.</sub>

### `04` &nbsp; GitHub pulse

{pic('generated','metrics','Public GitHub metrics automatically refreshed by Actions')}

{pic('generated','snake','Contribution snake graphic generated from public GitHub activity')}

<sub>GitHub activity reflects public data only.</sub>

### `05` &nbsp; Let’s connect

{pic('sections','footer','Connect on GitHub')}

<div align="center">

{(' &nbsp;·&nbsp; '.join(html_links))}


</div>
'''

def write_if_changed(path,content,check):
    if check:
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            print('OUT OF DATE:',path.relative_to(ROOT));return False
        return True
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        path.write_text(content,encoding='utf-8');print('updated:',path.relative_to(ROOT))
    return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true',help='Fail if generated assets need rebuilding');args=ap.parse_args()
    cfg=json.loads(CONFIG.read_text())
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}',cfg['username']):sys.exit('Invalid username')
    if len(cfg['projects'])!=4:sys.exit('Exactly 4 featured projects required in this design')
    ok=True
    assets={'README.md':markdown(cfg)}
    for mode,t in THEMES.items():
        dark=mode=='dark'
        assets[f'assets/hero/banner-{mode}.svg']=hero(cfg,t,dark)
        assets[f'assets/sections/terminal-{mode}.svg']=terminal(cfg,t,dark)
        assets[f'assets/sections/stack-{mode}.svg']=stack(cfg,t,dark)
        assets[f'assets/sections/footer-{mode}.svg']=footer(cfg,t,dark)
        for pr in cfg['projects']:
            assets[f'assets/projects/{pr["slug"]}-{mode}.svg']=project(pr,t,dark)
    for path,contents in assets.items():ok=write_if_changed(ROOT/path,contents,args.check) and ok
    if not ok:sys.exit(1)
    print(f'Profile {"checked" if args.check else "built"}: {len(assets)} files')

if __name__=='__main__':main()
