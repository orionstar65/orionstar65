#!/usr/bin/env python3
"""Optional, local-only dark and light PNG overview (pip install -r requirements-preview.txt)."""
import argparse
from io import BytesIO
from pathlib import Path
import sys
from build_profile import ROOT
try:
    import cairosvg
    from PIL import Image
except ImportError:
    sys.exit('Install preview dependencies: python3 -m pip install -r requirements-preview.txt')


def render(theme,out):
    rows=[
        ['assets/hero/banner-{}.svg'],
        ['assets/sections/terminal-{}.svg'],
        ['assets/sections/stack-{}.svg'],
        ['assets/projects/roleward-{}.svg','assets/projects/connectors-{}.svg'],
        ['assets/projects/travel-{}.svg','assets/projects/lab-{}.svg'],
        ['assets/generated/metrics-{}.svg'],
        ['assets/generated/snake-{}.svg'],
        ['assets/sections/footer-{}.svg'],
    ]
    scale=.78;space=18
    canvas=Image.new('RGB',(int(1320*scale),int(2560*scale)), '#071020' if theme=='dark' else '#F0F6FD')
    y=space
    for group in rows:
        imgs=[]
        for fmt in group:
            src=ROOT/fmt.format(theme)
            image=Image.open(BytesIO(cairosvg.svg2png(url=str(src)))).convert('RGBA')
            target_w=int((620 if len(group)==2 else 1280)*scale)
            imgs.append(image.resize((target_w,int(image.height*target_w/image.width)),Image.Resampling.LANCZOS))
        for j,img in enumerate(imgs):
            x=space+j*(imgs[0].width+space)
            canvas.paste(img,(x,y),img)
        y+=max(img.height for img in imgs)+space
    canvas=canvas.crop((0,0,canvas.width,y+space))
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,optimize=True)
    print(out,'\nsize:',canvas.size)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--theme',choices=['dark','light','both'],default='both');args=ap.parse_args()
    for mode in (['dark','light'] if args.theme=='both' else [args.theme]):render(mode,ROOT/f'assets/preview-{mode}.png')

if __name__=='__main__':main()
