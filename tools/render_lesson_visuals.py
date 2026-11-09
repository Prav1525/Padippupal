#!/usr/bin/env python3
"""Render original, child-friendly PadippuPal diagrams as phone-first PNGs.

Manifest item: lesson_id, module_key, step_ids, title, alt_text, layout, panels.
Each panel: heading, diagram (one of the supported types), optional labels/values.
A pair is two separate full-width 1080x720 PNGs, never side-by-side.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 720
BG, INK, MUTED, BLUE = "#FFFDF7", "#24324A", "#65738A", "#277DA1"
PALETTE = ["#E8F4F8", "#FFF0D9", "#EAF4E4", "#F3EAFE"]
FONT_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
BOLD_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]

def font(size, bold=False):
    for path in (BOLD_CANDIDATES if bold else FONT_CANDIDATES):
        if Path(path).exists(): return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def label(d, xy, text, size=27, color=INK, bold=False, anchor=None):
    d.text(xy, str(text), font=font(size, bold), fill=color, anchor=anchor)

def arrow(d, a, b, fill=BLUE, width=8):
    d.line((a, b), fill=fill, width=width)
    ang = math.atan2(b[1]-a[1], b[0]-a[0])
    for delta in (2.55, -2.55):
        p = (b[0]+24*math.cos(ang+delta), b[1]+24*math.sin(ang+delta))
        d.line((b, p), fill=fill, width=width)

def diagram(d, kind, data):
    # All drawings are deliberately simple: large objects, short labels, no tiny legend.
    if kind == "fractions":
        cx, cy, r = 300, 430, 190
        n = int(data.get("parts", 4)); shaded = int(data.get("shaded", 1))
        if not 2 <= n <= 12 or not 0 <= shaded <= n: raise ValueError("fractions needs parts 2..12 and shaded 0..parts")
        for i in range(n):
            a0, a1 = -90+i*360/n, -90+(i+1)*360/n
            d.pieslice((cx-r,cy-r,cx+r,cy+r), a0, a1, fill="#F6C66A" if i < shaded else "#E8F4F8", outline=INK, width=5)
        d.ellipse((cx-r,cy-r,cx+r,cy+r), outline=INK, width=5)
        label(d,(590,355),f"{shaded}/{n}",76,BLUE,True)
        label(d,(590,445),"equal parts",34)
    elif kind == "rectangle_properties":
        d.rectangle((240,235,840,545),fill="#E8F4F8",outline=INK,width=8)
        label(d,(540,385),"RECTANGLE",40,INK,True,anchor="mm")
        label(d,(540,190),"Opposite sides are equal",31,BLUE,True,anchor="mm")
        label(d,(540,590),"Each corner = 90°",30,INK,True,anchor="mm")
        for x,y in [(240,235),(840,235),(240,545),(840,545)]:
            d.rectangle((x+(18 if x==240 else -58),y+(18 if y==235 else -58),x+(58 if x==240 else -18),y+(58 if y==235 else -18)),outline="#D35D6E",width=4)
    elif kind == "decantation":
        for cx in (320,760):
            d.polygon([(cx-110,245),(cx+110,245),(cx+82,545),(cx-82,545)],fill="#D8EDF5",outline=INK)
        d.rectangle((220,380,420,540),fill="#D7B37A",outline="#9B7545",width=2)
        d.rectangle((660,380,860,540),fill="#BFE4F2",outline="#6CA9D6",width=2)
        arrow(d,(445,365),(630,260))
        label(d,(320,600),"MIXTURE SETTLES",25,INK,True,anchor="mm")
        label(d,(760,600),"POUR CLEAR LIQUID",25,INK,True,anchor="mm")

    elif kind == "scientific_method":
        steps=["OBSERVE","ASK","GUESS","TEST","CONCLUDE"]
        xs=[145,340,535,730,925]
        for i,(x,t) in enumerate(zip(xs,steps)):
            d.rounded_rectangle((x-82,340,x+82,470),radius=22,fill=PALETTE[i%4],outline=INK,width=4)
            label(d,(x,405),t,22,INK,True,anchor="mm")
            if i<4: arrow(d,(x+86,405),(xs[i+1]-88,405))
        label(d,(540,225),"A simple way scientists investigate questions",31,BLUE,True,anchor="mm")
    elif kind == "angle":
        o=(300,500); p=(760,500); q=(650,210)
        d.line((o,p),fill=BLUE,width=12); d.line((o,q),fill="#E39A35",width=12)
        d.ellipse((o[0]-12,o[1]-12,o[0]+12,o[1]+12),fill=INK)
        d.arc((o[0]-145,o[1]-145,o[0]+145,o[1]+145),-68,0,fill=INK,width=7)
        label(d,(260,545),"VERTEX",25,INK,True); label(d,(775,490),"ARM",25,BLUE,True)
        label(d,(600,175),"ARM",25,"#B36A12",True)
    elif kind == "four_point_lines":
        points = {"A": (300, 230), "B": (790, 230), "C": (790, 535), "D": (300, 535)}
        pairs = [("A","B"),("A","C"),("A","D"),("B","C"),("B","D"),("C","D")]
        for left, right in pairs:
            d.line((*points[left], *points[right]), fill=BLUE, width=7)
        for name, (x, y) in points.items():
            d.ellipse((x-13,y-13,x+13,y+13), fill="#E39A35", outline=INK, width=3)
            label(d,(x-24 if name in ("A","D") else x+24,y-28),name,28,INK,True,anchor="mm")
        label(d,(545,625),"4 points • 6 joining lines",30,INK,True,anchor="mm")
    elif kind == "area_perimeter":
        x0,y0,x1,y1=180,220,850,560
        d.rectangle((x0,y0,x1,y1),fill="#E8F4F8",outline=INK,width=8)
        for x in range(x0+67,x1,67): d.line((x,y0,x,y1),fill="#A7C9D8",width=2)
        for y in range(y0+68,y1,68): d.line((x0,y,x1,y),fill="#A7C9D8",width=2)
        label(d,(515,590),data.get("length","6 units"),30,BLUE,True,anchor="mm")
        label(d,(110,390),data.get("width","3 units"),28,BLUE,True,anchor="mm")
        label(d,(515,380),"AREA = inside",38,INK,True,anchor="mm")
    elif kind == "perimeter_shapes":
        # Make the outside boundary the focus; do not show an area grid here.
        d.rectangle((95,300,365,470),fill="#E8F4F8",outline=BLUE,width=10)
        label(d,(230,245),"RECTANGLE",27,INK,True,anchor="mm")
        label(d,(230,520),"6 + 3 + 6 + 3 = 18",23,BLUE,True,anchor="mm")
        d.polygon([(540,260),(405,485),(675,485)],fill="#FFF0D9",outline=BLUE)
        label(d,(540,225),"TRIANGLE",27,INK,True,anchor="mm")
        label(d,(540,535),"4 + 4 + 4 = 12",23,BLUE,True,anchor="mm")
        pts=[(850,275),(955,335),(955,455),(850,515),(745,455),(745,335)]
        d.polygon(pts,fill="#EAF4E4",outline=BLUE)
        label(d,(850,235),"HEXAGON",27,INK,True,anchor="mm")
        label(d,(850,560),"2 on each side = 12",23,BLUE,True,anchor="mm")
        label(d,(540,625),"Perimeter = add every outside side",28,INK,True,anchor="mm")
    elif kind == "same_area_perimeters":
        # Textbook example: equal areas, different boundary lengths.
        d.rounded_rectangle((45,205,520,600),radius=24,fill="#F8FBFC",outline="#C8DCE5",width=3)
        d.rounded_rectangle((560,205,1035,600),radius=24,fill="#F8FBFC",outline="#C8DCE5",width=3)
        d.rectangle((120,300,420,478),fill="#E8F4F8",outline=BLUE,width=7)
        d.rectangle((685,280,910,472),fill="#FFF0D9",outline=BLUE,width=7)
        label(d,(282,245),"HOUSE A",27,INK,True,anchor="mm")
        label(d,(797,245),"HOUSE B",27,INK,True,anchor="mm")
        label(d,(282,485),"42 ft × 25 ft",25,INK,True,anchor="mm")
        label(d,(282,520),"Area = 1,050 sq ft",24,BLUE,True,anchor="mm")
        label(d,(282,555),"Perimeter = 134 ft",24,INK,True,anchor="mm")
        label(d,(797,495),"35 ft × 30 ft",25,INK,True,anchor="mm")
        label(d,(797,530),"Area = 1,050 sq ft",24,BLUE,True,anchor="mm")
        label(d,(797,565),"Perimeter = 130 ft",24,INK,True,anchor="mm")
    elif kind == "shared_prime_factors":
        # Two numbers share 3 and 7, so this pair is not co-prime.
        label(d,(270,205),"NUMBER A = 42",30,INK,True,anchor="mm")
        label(d,(810,205),"NUMBER B = 231",30,INK,True,anchor="mm")
        left=[("2",False),("3",True),("7",True)]
        right=[("3",True),("7",True),("11",False)]
        for i,(v,shared) in enumerate(left):
            x=120+i*170
            d.rounded_rectangle((x,290,x+125,410),radius=20,fill="#F6C66B" if shared else "#E8F4F8",outline=INK,width=4)
            label(d,(x+62,350),v,42,INK,True,anchor="mm")
        for i,(v,shared) in enumerate(right):
            x=660+i*130
            d.rounded_rectangle((x,290,x+110,410),radius=20,fill="#F6C66B" if shared else "#E8F4F8",outline=INK,width=4)
            label(d,(x+55,350),v,42,INK,True,anchor="mm")
        label(d,(270,455),"2 × 3 × 7 = 42",26,BLUE,True,anchor="mm")
        label(d,(810,455),"3 × 7 × 11 = 231",26,BLUE,True,anchor="mm")
        label(d,(540,555),"Shared prime factors: 3 and 7",30,INK,True,anchor="mm")
        label(d,(540,610),"So the numbers are NOT co-prime",27,"#B43B51",True,anchor="mm")
    elif kind == "condensation_examples":
        # Examples of droplets appearing on cool surfaces.
        d.rounded_rectangle((70,250,370,560),radius=28,fill="#E8F4F8",outline=INK,width=5)
        d.rounded_rectangle((430,250,650,560),radius=28,fill="#D9EAF2",outline=INK,width=5)
        d.rectangle((750,440,1010,560),fill="#B7D7A8",outline=INK,width=4)
        for x,y in [(120,315),(180,365),(300,330),(485,330),(590,385),(835,425),(920,405)]:
            d.ellipse((x-10,y-10,x+10,y+10),fill="#6CA9D6",outline=INK,width=2)
        d.ellipse((790,290,970,410),fill="#8BCB83",outline="#286B3A",width=4)
        d.line((805,380,955,320),fill="#286B3A",width=4)
        for x in (790,850,910,970): d.line((x,555,x-18,475),fill="#39834A",width=5)
        label(d,(220,210),"COOL BOTTLE",25,INK,True,anchor="mm")
        label(d,(540,210),"COLD GLASS",25,INK,True,anchor="mm")
        label(d,(880,245),"LEAF DEW",25,INK,True,anchor="mm")
        label(d,(540,625),"Water vapour forms droplets on cool surfaces",27,BLUE,True,anchor="mm")
    elif kind == "condensation_process":
        # Vapour cools and condenses into tiny liquid droplets.
        for x in (170,235,300,365):
            for y in (300,360,420):
                d.ellipse((x-9,y-9,x+9,y+9),fill="#8DBBE8",outline=INK,width=2)
        label(d,(270,245),"WATER VAPOUR",25,INK,True,anchor="mm")
        arrow(d,(420,365),(545,365),fill=BLUE,width=8)
        d.rounded_rectangle((560,260,745,475),radius=28,fill="#E8F4F8",outline=INK,width=5)
        label(d,(652,365),"COOLING",26,INK,True,anchor="mm")
        arrow(d,(760,365),(850,365),fill=BLUE,width=8)
        d.ellipse((870,270,1020,420),fill="#DCE7F4",outline=INK,width=4)
        for x,y in [(900,320),(950,300),(985,345),(925,375),(975,390)]:
            d.ellipse((x-12,y-12,x+12,y+12),fill="#6CA9D6",outline=INK,width=2)
        label(d,(945,455),"TINY DROPLETS",23,INK,True,anchor="mm")
        label(d,(540,570),"Water vapour changes into liquid water",29,BLUE,True,anchor="mm")

    elif kind == "symmetry":
        box=(220,180,860,570); d.ellipse(box,fill="#F6C66A",outline=INK,width=6)
        d.polygon([(540,205),(420,330),(540,410),(660,330)],fill="#E8F4F8",outline=INK)
        d.line((540,150,540,600),fill="#D35D6E",width=8)
        label(d,(565,145),"FOLD LINE",27,"#B43B51",True)
        label(d,(540,625),"Both sides match",34,INK,True,anchor="mm")
    elif kind == "bar_graph":
        vals=data.get("values",[3,5,2,4]); names=data.get("labels",["A","B","C","D"])
        if len(vals)!=len(names) or not 2<=len(vals)<=5 or any(not isinstance(v,int) or v<0 or v>8 for v in vals): raise ValueError("bar_graph needs 2–5 labels and integer values 0–8")
        xbase,ybase=220,565; d.line((xbase,180,xbase,ybase),fill=INK,width=6); d.line((xbase,ybase,900,ybase),fill=INK,width=6)
        for i,v in enumerate(vals):
            x=xbase+90+i*145; top=ybase-v*43
            d.rounded_rectangle((x,top,x+72,ybase),radius=12,fill=PALETTE[i%4],outline=BLUE,width=4)
            label(d,(x+36,top-34),v,25,INK,True,anchor="mm"); label(d,(x+36,ybase+32),names[i],23,INK,True,anchor="mm")

    elif kind == "water_states":
        xs=[190,540,890]; colors=["#CDEAF5","#8BC9E8","#DCE7F4"]; names=["ICE","LIQUID","VAPOUR"]
        for x,c,nm in zip(xs,colors,names):
            d.rounded_rectangle((x-115,300,x+115,500),radius=28,fill=c,outline=INK,width=5)
            label(d,(x,400),nm.replace("\n"," "),28,INK,True,anchor="mm")
        arrow(d,(320,400),(405,400)); arrow(d,(670,400),(755,400))
        label(d,(540,190),"Heat can change the state of water",28,BLUE,True,anchor="mm")
    elif kind == "seedling":
        d.line((540,350,540,555),fill="#39834A",width=15)
        d.ellipse((420,245,540,365),fill="#8BCB83",outline="#286B3A",width=5)
        d.ellipse((540,245,660,365),fill="#8BCB83",outline="#286B3A",width=5)
        d.line((540,555,440,650),fill="#A97945",width=10); d.line((540,555,640,650),fill="#A97945",width=10)
        d.line((490,605,470,670),fill="#A97945",width=7); d.line((590,605,610,670),fill="#A97945",width=7)
        label(d,(700,285),"SHOOTS & LEAVES",26,INK,True)
        label(d,(700,520),"ROOTS GROW DOWN",26,INK,True)
        label(d,(540,175),"A seedling begins to grow",34,BLUE,True,anchor="mm")
    elif kind == "plant":
        d.line((540,250,540,520),fill="#39834A",width=18)
        for x,y,side in [(420,340,-1),(660,400,1),(430,445,-1)]:
            d.ellipse((min(x,540),y-55,max(x,540),y+55),fill="#8BCB83",outline="#286B3A",width=5)
        d.ellipse((475,155,605,285),fill="#F5C66B",outline=INK,width=5)
        for i in range(6):
            a=i*math.pi/3; px=540+72*math.cos(a); py=220+72*math.sin(a)
            d.ellipse((px-28,py-28,px+28,py+28),fill="#E99AA8",outline=INK,width=3)
        d.line((540,520,420,625),fill="#A97945",width=10); d.line((540,520,650,625),fill="#A97945",width=10)
        label(d,(700,205),"FLOWER",26,INK,True); label(d,(700,355),"LEAF",26,INK,True)
        label(d,(700,500),"STEM",26,INK,True); label(d,(350,615),"ROOTS",26,INK,True)
    elif kind == "magnet":
        d.rounded_rectangle((260,280,820,430),radius=28,fill="#F2C7C7",outline=INK,width=6)
        d.rectangle((260,280,540,430),fill="#E98A8A",outline=INK,width=4); d.rectangle((540,280,820,430),fill="#8DBBE8",outline=INK,width=4)
        label(d,(400,355),"N",58,INK,True,anchor="mm"); label(d,(680,355),"S",58,INK,True,anchor="mm")
        for x,y in [(230,210),(870,210),(220,510),(870,510)]:
            d.line((x-22,y+18,x+22,y-18),fill="#8A929B",width=9)
            d.line((x-27,y+23,x-18,y+14),fill="#5E6873",width=12)
            d.polygon([(x+22,y-18),(x+33,y-29),(x+27,y-12)],fill="#5E6873")
        label(d,(540,560),"Iron objects are attracted",32,BLUE,True,anchor="mm")
    elif kind == "separation":
        # Simple sieve and filter funnel sequence.
        d.polygon([(180,250),(480,250),(420,390),(240,390)],fill="#F6DCA9",outline=INK)
        for x in range(240,430,45): d.line((x,260,x+20,380),fill="#9A7A45",width=3)
        label(d,(330,445),"SIEVING",30,INK,True,anchor="mm")
        d.polygon([(650,220),(900,220),(800,390)],fill="#D7EAF2",outline=INK)
        d.line((680,280,870,280),fill="#B28A5C",width=7); d.line((800,390,800,540),fill=BLUE,width=8)
        label(d,(780,590),"FILTERING",30,INK,True,anchor="mm")
    elif kind == "thermometer":
        d.rounded_rectangle((470,170,610,540),radius=65,fill="#F2F5F7",outline=INK,width=6)
        d.ellipse((430,475,650,695),fill="#E46B5D",outline=INK,width=6)
        d.rectangle((520,310,560,565),fill="#E46B5D")
        for i,t in enumerate(["0°","20°","40°","60°","80°","100°"]):
            y=520-i*60; d.line((610,y,670,y),fill=INK,width=4); label(d,(690,y-16),t,24,INK)

    elif kind == "ruler_measurement":
        d.rounded_rectangle((130,390,950,500),radius=18,fill="#F4D98D",outline=INK,width=5)
        for i in range(41):
            x=150+i*19; h=62 if i%10==0 else (42 if i%5==0 else 22)
            d.line((x,400,x,400+h),fill=INK,width=3)
        for i,t in enumerate(["0","10","20","30","40"]): label(d,(150+i*190,525),t,25,INK,True,anchor="mm")
        d.rounded_rectangle((150,300,530,365),radius=12,fill="#E7A76A",outline=INK,width=4)
        label(d,(540,210),"Start at zero; read the mark at the other end",28,BLUE,True,anchor="mm")
        label(d,(540,585),"Example object length: 20 cm",25,INK,True,anchor="mm")
    elif kind == "sun_energy":
        d.ellipse((180,300,390,510),fill="#F6C66B",outline=INK,width=5)
        d.ellipse((760,330,900,470),fill="#7FA9D8",outline=INK,width=5)
        for y in [330,390,450]: arrow(d,(420,y),(735,y),fill="#E39A35",width=6)
        label(d,(285,555),"SUN",28,INK,True,anchor="mm")
        label(d,(830,520),"EARTH",25,INK,True,anchor="mm")
        label(d,(540,220),"Energy travels from the Sun to Earth",30,BLUE,True,anchor="mm")
    elif kind == "number_line":
        d.line((160,410,920,410),fill=INK,width=7)
        for n in range(-4,5):
            x=540+n*85; d.line((x,390,x,430),fill=INK,width=5); label(d,(x,455),n,26,INK,True,anchor="mm")
        d.ellipse((518,388,562,432),fill="#E98A8A",outline=INK,width=3)
        label(d,(540,290),"Zero is the middle",34,BLUE,True,anchor="mm")
    elif kind == "orbit":
        d.ellipse((280,190,800,650),outline="#8DBBE8",width=6)
        d.ellipse((500,390,600,490),fill="#F6C66B",outline=INK,width=4)
        d.ellipse((735,390,790,445),fill="#7FA9D8",outline=INK,width=3)
        label(d,(550,350),"SUN",26,INK,True,anchor="mm"); label(d,(760,475),"EARTH",24,INK,True,anchor="mm")
        label(d,(540,125),"Earth moves around the Sun",34,BLUE,True,anchor="mm")
    elif kind == "solar_system":
        # Eight planets in order; relative sizes and distances are schematic.
        names=["SUN","Mercury","Venus","Earth","Mars","Jupiter","Saturn","Uranus","Neptune"]
        xs=[130,260,350,445,535,640,755,865,975]
        radii=[43,8,13,14,10,29,25,19,18]
        cols=["#F6C66B","#9B8B78","#D6B078","#6CA9D6","#D98C6B","#C99A6B","#D9C18D","#8DC7CF","#547DB5"]
        for x,r,col,name in zip(xs,radii,cols,names):
            d.ellipse((x-r,350-r,x+r,350+r),fill=col,outline=INK,width=2)
            label(d,(x,445),name,17,INK,True,anchor="mm")
        label(d,(540,570),"Planets travel around the Sun",29,BLUE,True,anchor="mm")
        label(d,(540,620),"Schematic — sizes and distances are not to scale",20,MUTED,anchor="mm")
    elif kind == "constellation":
        pts=[(260,420),(390,270),(530,340),(690,190),(820,390),(650,520),(450,560)]
        for a,b in zip(pts,pts[1:]): d.line((a,b),fill="#8DBBE8",width=5)
        for x,y in pts: d.ellipse((x-15,y-15,x+15,y+15),fill="#F6C66B",outline=INK,width=3)
        label(d,(540,625),"A constellation is a recognised star pattern",25,INK,anchor="mm")
    elif kind == "leaf_venation":
        for cx,cy,parallel in [(350,410,False),(740,410,True)]:
            d.ellipse((cx-120,cy-205,cx+120,cy+205),fill="#9ACB87",outline="#286B3A",width=5)
            d.line((cx,cy+190,cx,cy-185),fill="#286B3A",width=8)
            if parallel:
                for dx in [-75,-40,40,75]: d.line((cx,cy+165,cx+dx,cy-155),fill="#397B48",width=4)
            else:
                for side in [-1,1]:
                    for y in range(-100,140,55):
                        d.line((cx,cy-y,cx+side*90,cy-y-45),fill="#397B48",width=4)
        label(d,(350,650),"NET-LIKE",26,INK,True,anchor="mm")
        label(d,(740,650),"PARALLEL",26,INK,True,anchor="mm")
    elif kind == "solubility":
        for cx,fill,txt in [(330,"#BFE4F2","SALT + WATER"),(750,"#BFE4F2","SAND + WATER")]:
            d.rounded_rectangle((cx-105,260,cx+105,555),radius=24,fill=fill,outline=INK,width=5)
            d.line((cx-85,390,cx+85,390),fill="#6CA9D6",width=5)
            if "SAND" in txt:
                d.ellipse((cx-80,505,cx+80,530),fill="#C9A36B",outline="#98713D",width=2)
            else:
                for x in range(cx-55,cx+60,35): d.ellipse((x,420,x+8,428),fill="#FFFFFF")
            label(d,(cx,590),txt,23,INK,True,anchor="mm")
        label(d,(540,175),"Some materials dissolve; others do not",30,BLUE,True,anchor="mm")
    elif kind == "food_variety":
        cards=[(160,230,"FRUITS","#F6C66B"),(570,230,"VEGETABLES","#9ACB87"),
               (160,430,"GRAINS","#E8C48B"),(570,430,"PROTEIN","#E99AA8")]
        for x,y,name,col in cards:
            d.rounded_rectangle((x,y,x+350,y+135),radius=24,fill=col,outline=INK,width=4)
            cx,cy=x+82,y+67
            if name=="FRUITS":
                d.ellipse((cx-31,cy-34,cx+31,cy+34),fill="#D95D50",outline=INK,width=3)
                d.line((cx,cy-30,cx+8,cy-48),fill="#795438",width=6)
                d.ellipse((cx+5,cy-48,cx+35,cy-35),fill="#4C9B58",outline=INK,width=2)
            elif name=="VEGETABLES":
                d.polygon([(cx,cy+42),(cx-27,cy-25),(cx+27,cy-25)],fill="#E58B3C",outline=INK)
                d.line((cx,cy-20,cx-15,cy-48),fill="#39834A",width=7)
                d.line((cx,cy-20,cx+16,cy-50),fill="#39834A",width=7)
            elif name=="GRAINS":
                d.line((cx,cy+43,cx,cy-42),fill="#98713D",width=6)
                for yy in [-28,-8,12,30]:
                    d.ellipse((cx-23,cy+yy-9,cx-4,cy+yy+9),fill="#D6A94F",outline=INK,width=2)
                    d.ellipse((cx+4,cy+yy-9,cx+23,cy+yy+9),fill="#D6A94F",outline=INK,width=2)
            else:
                d.ellipse((cx-34,cy-42,cx+34,cy+42),fill="#FFFFFF",outline=INK,width=3)
                d.ellipse((cx-16,cy-16,cx+16,cy+16),fill="#F2C34E",outline="#B88924",width=2)
            label(d,(x+235,y+68),name,24,INK,True,anchor="mm")
        label(d,(540,625),"A variety of foods helps make a balanced diet",27,BLUE,True,anchor="mm")
    elif kind == "factor_tree":
        # Verified textbook example: 72 = 2 x 2 x 2 x 3 x 3.
        nodes=[(540,235,"72"),(350,390,"8"),(730,390,"9"),
               (245,540,"2"),(445,540,"4"),(660,540,"3"),(820,540,"3"),
               (385,650,"2"),(500,650,"2")]
        edges=[((540,285),(350,340)),((540,285),(730,340)),
               ((350,440),(245,500)),((350,440),(445,500)),
               ((730,440),(660,500)),((730,440),(820,500)),
               ((445,590),(385,615)),((445,590),(500,615))]
        for a,b in edges: d.line((a,b),fill=BLUE,width=6)
        for x,y,t in nodes:
            rad=36 if t in ("2","3") else (50 if t=="4" else 54)
            d.ellipse((x-rad,y-rad,x+rad,y+rad),fill="#F6C66B" if t=="72" else "#E8F4F8",outline=INK,width=4)
            label(d,(x,y),t,34,INK,True,anchor="mm")


    elif kind == "triangle_pattern":
        for row in range(1,5):
            for col in range(row):
                x=540+(col-(row-1)/2)*100; y=250+row*85
                d.polygon([(x,y-42),(x-42,y+32),(x+42,y+32)],fill=PALETTE[(row+col)%4],outline=INK)
        label(d,(540,190),"Each new row adds one triangle",28,BLUE,True,anchor="mm")
    elif kind == "number_ray":
        d.line((150,430,930,430),fill=INK,width=7)
        arrow(d,(170,430),(925,430))
        for n in range(0,9):
            x=180+n*88; d.line((x,405,x,455),fill=INK,width=4); label(d,(x,480),n,26,INK,True,anchor="mm")
        label(d,(180,350),"START",24,BLUE,True,anchor="mm")
        label(d,(720,290),"Counting numbers move to the right",30,BLUE,True,anchor="mm")
    elif kind == "perimeter_rectangle":
        x0,y0,x1,y1=220,260,860,520
        d.rectangle((x0,y0,x1,y1),fill="#E8F4F8",outline=INK,width=8)
        label(d,(540,220),f"Length = {data.get('length',12)} cm",30,BLUE,True,anchor="mm")
        label(d,(540,565),f"Perimeter = 2 × ({data.get('length',12)} + {data.get('breadth',8)}) cm",27,INK,True,anchor="mm")
        label(d,(155,390),f"{data.get('breadth',8)} cm",27,BLUE,True,anchor="mm")
        label(d,(925,390),f"{data.get('breadth',8)} cm",27,BLUE,True,anchor="mm")
        label(d,(540,390),"Add all four sides",30,INK,True,anchor="mm")
    elif kind == "nutrient_sources":
        cards=[(130,250,"FRUITS","#F6C66B"),(570,250,"GREEN VEG","#9ACB87"),(130,440,"WHOLE GRAINS","#E8C48B"),(570,440,"LEAFY VEG","#8BCB83")]
        for x,y,name,col in cards:
            d.rounded_rectangle((x,y,x+370,y+125),radius=22,fill=col,outline=INK,width=4)
            label(d,(x+185,y+62),name,26,INK,True,anchor="mm")
        label(d,(540,190),"Vitamins and roughage come from plant foods",28,BLUE,True,anchor="mm")
    elif kind == "tea_filter":
        d.polygon([(300,250),(780,250),(600,470),(480,470)],fill="#F3EAFE",outline=INK)
        d.line((480,470,600,470),fill=INK,width=7)
        d.line((540,470,540,590),fill=BLUE,width=8)
        for x in range(400,690,45): d.ellipse((x,290,x+18,308),fill="#9B7545",outline=INK)
        d.rounded_rectangle((455,590,625,655),radius=16,fill="#BFE4F2",outline=INK,width=4)
        label(d,(540,210),"Cloth catches tea leaves; tea passes through",27,BLUE,True,anchor="mm")
        label(d,(540,680),"FILTERED TEA",22,INK,True,anchor="mm")
    elif kind == "seed_germination":
        d.line((540,360,540,530),fill="#39834A",width=13)
        d.ellipse((445,280,540,375),fill="#8BCB83",outline="#286B3A",width=4)
        d.ellipse((540,280,635,375),fill="#8BCB83",outline="#286B3A",width=4)
        d.line((540,530,475,635),fill="#A97945",width=9); d.line((540,530,605,635),fill="#A97945",width=9)
        d.ellipse((500,485,580,555),fill="#C9A36B",outline=INK,width=4)
        label(d,(540,205),"A seed sprouts when it gets water and air",29,BLUE,True,anchor="mm")
        label(d,(770,330),"SHOOT",25,INK,True); label(d,(740,590),"ROOT",25,INK,True)
    elif kind == "fraction_number_line":
        d.line((150,430,930,430),fill=INK,width=7)
        for i in range(5):
            x=180+i*180; d.line((x,405,x,455),fill=INK,width=4); label(d,(x,485),["0","1/4","1/2","3/4","1"][i],26,INK,True,anchor="mm")
        d.ellipse((522,410,558,446),fill="#E98A8A",outline=INK,width=3)
        label(d,(540,300),"Fractions mark equal parts between 0 and 1",28,BLUE,True,anchor="mm")
    elif kind == "equivalent_fractions":
        for y,parts,shaded,txt in [(300,2,1,"1/2"),(440,4,2,"2/4"),(580,6,3,"3/6")]:
            x0=250; width=500/parts
            for i in range(parts):
                d.rectangle((x0+i*width,y-38,x0+(i+1)*width,y+38),fill="#F6C66B" if i<shaded else "#E8F4F8",outline=INK,width=4)
            label(d,(820,y),txt,30,BLUE,True,anchor="mm")
        label(d,(540,205),"Different names can show the same share",29,BLUE,True,anchor="mm")
    elif kind == "fraction_addition":
        for y,parts,shaded,txt in [(320,3,1,"1/3"),(450,3,1,"+ 1/3"),(590,3,2,"= 2/3")]:
            for i in range(parts):
                x=280+i*175
                d.rectangle((x,y-35,x+175,y+35),fill="#F6C66B" if i<shaded else "#E8F4F8",outline=INK,width=4)
            label(d,(900,y),txt,29,BLUE,True,anchor="mm")
    elif kind == "fraction_compare":
        for y,shaded,txt in [(350,4,"4/7"),(520,5,"5/7")]:
            for i in range(7):
                x=220+i*92
                d.rectangle((x,y-32,x+92,y+32),fill="#F6C66B" if i<shaded else "#E8F4F8",outline=INK,width=3)
            label(d,(900,y),txt,30,BLUE,True,anchor="mm")
        label(d,(540,220),"Same denominator: compare the shaded parts",28,BLUE,True,anchor="mm")
    elif kind == "protractor":
        d.arc((250,260,830,840),180,360,fill=INK,width=8)
        d.line((540,550,250,550),fill=BLUE,width=8)
        d.line((540,550,540,260),fill="#E39A35",width=8)
        d.ellipse((525,535,555,565),fill=INK)
        for deg in range(0,181,10):
            a=math.radians(180-deg); x1=540+250*math.cos(a); y1=550-250*math.sin(a); x2=540+275*math.cos(a); y2=550-275*math.sin(a)
            d.line((x1,y1,x2,y2),fill=INK,width=3)
        label(d,(540,210),"Place the centre on the vertex; read from zero",26,BLUE,True,anchor="mm")
        label(d,(260,600),"0°",24,INK,True); label(d,(800,600),"180°",24,INK,True)
    elif kind == "clock_angles":
        for cx,cy,angle,txt in [(320,420,90,"90°"),(760,420,180,"180°")]:
            d.ellipse((cx-135,cy-135,cx+135,cy+135),outline=INK,width=6)
            d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=INK)
            d.line((cx,cy,cx,cy-105),fill=BLUE,width=9)
            a=math.radians(angle-90); d.line((cx,cy,cx+105*math.cos(a),cy+105*math.sin(a)),fill="#E39A35",width=9)
            label(d,(cx,cy+175),txt,30,BLUE,True,anchor="mm")
    elif kind == "number_patterns":
        for row,(name,vals) in enumerate([("SQUARES",[1,4,9]),("TRIANGLES",[1,3,6])]):
            y=300+row*210; label(d,(170,y),name,25,BLUE,True)
            for j,v in enumerate(vals):
                cx=420+j*210
                if row==0:
                    side=int(math.sqrt(v))
                    for k in range(v):
                        xx=cx+(k%side)*28-(side*14); yy=y-20+(k//side)*28
                        d.rectangle((xx,yy,xx+25,yy+25),fill=PALETTE[j%4],outline=INK,width=2)
                else:
                    for k in range(v):
                        xx=cx+(k%3)*28-28; yy=y-20+(k//3)*28
                        d.ellipse((xx,yy,xx+22,yy+22),fill=PALETTE[j%4],outline=INK,width=2)
                label(d,(cx,y+95),v,22,INK,True,anchor="mm")
    elif kind == "odd_numbers_square":
        for row in range(6):
            for col in range(6):
                d.rectangle((270+col*65,220+row*65,330+col*65,280+row*65),fill=PALETTE[(row+col)%4],outline=INK,width=2)
        label(d,(540,650),"1 + 3 + 5 + 7 + 9 + 11 = 36",28,BLUE,True,anchor="mm")
    elif kind == "square_growth":
        for idx,n in enumerate([1,2,3]):
            x=170+idx*300; y=300
            for row in range(n):
                for col in range(n):
                    d.rectangle((x+col*65,y+row*65,x+col*65+60,y+row*65+60),fill=PALETTE[(row+col)%4],outline=INK,width=2)
            label(d,(x+(n*65)/2,y+n*65+45),f"{n} × {n} = {n*n}",25,BLUE,True,anchor="mm")
    elif kind == "polygon_perimeter":
        d.polygon([(300,300),(500,300),(400,470)],fill="#E8F4F8",outline=INK)
        d.polygon([(700,270),(820,340),(820,470),(700,540),(580,470),(580,340)],fill="#FFF0D9",outline=INK)
        label(d,(400,560),"3 equal sides",25,BLUE,True,anchor="mm"); label(d,(700,600),"6 equal sides",25,BLUE,True,anchor="mm")
        label(d,(540,205),"Perimeter is the total distance around",29,BLUE,True,anchor="mm")
    elif kind == "tangram":
        pts=[(330,250),(540,250),(540,460),(330,460)]
        d.polygon(pts,fill="#F6C66B",outline=INK)
        d.line((330,250,540,460),fill=INK,width=4); d.line((540,250,330,460),fill=INK,width=4)
        d.polygon([(650,260),(850,260),(850,460),(650,460)],fill="#E8F4F8",outline=INK)
        d.line((650,260,850,460),fill=INK,width=4); d.line((750,260,750,460),fill=INK,width=4)
        label(d,(540,570),"Same pieces can make different shapes",28,BLUE,True,anchor="mm")
    elif kind == "grid_area":
        x0,y0=270,230
        for row in range(5):
            for col in range(7):
                fill="#F6C66B" if (row<3 and col<5) else "#E8F4F8"
                d.rectangle((x0+col*70,y0+row*70,x0+(col+1)*70,y0+(row+1)*70),fill=fill,outline=INK,width=2)
        label(d,(540,640),"Count the unit squares inside the shape",28,BLUE,True,anchor="mm")
    elif kind == "factor_arrays":
        for row,(n,cols,txt) in enumerate([(12,4,"12 = 3 × 4"),(7,7,"7 has only 1 and 7")]):
            y=300+row*220; label(d,(160,y),txt,27,BLUE,True)
            for i in range(n):
                x=500+(i%cols)*42; yy=y-45+(i//cols)*42
                d.ellipse((x,yy,x+32,yy+32),fill=PALETTE[row],outline=INK,width=2)
    elif kind == "even_numbers":
        for i,n in enumerate([10,12,14,16,18]):
            x=170+i*180
            d.rounded_rectangle((x-55,330,x+55,440),radius=18,fill=PALETTE[i%4],outline=INK,width=4)
            label(d,(x,385),n,32,INK,True,anchor="mm")
        label(d,(540,550),"Each number ends in 0, 2, 4, 6 or 8",28,BLUE,True,anchor="mm")
    elif kind == "building_floors":
        d.rectangle((430,230,650,610),fill="#E8F4F8",outline=INK,width=5)
        for i in range(5):
            y=250+i*72; d.line((430,y,650,y),fill=INK,width=3)
            label(d,(540,y+28),["+2","+1","GROUND","−1","−2"][i],25,INK,True,anchor="mm")
        label(d,(760,330),"Above ground: positive",24,BLUE,True)
        label(d,(760,510),"Below ground: negative",24,BLUE,True)
    elif kind == "integer_movement":
        d.line((160,440,920,440),fill=INK,width=6)
        for n in range(-4,5):
            x=540+n*90; d.line((x,420,x,460),fill=INK,width=4); label(d,(x,490),n,24,INK,True,anchor="mm")
        arrow(d,(900,350),(360,350),fill="#D35D6E",width=9)
        label(d,(620,300),"Move left: numbers get smaller",27,BLUE,True,anchor="mm")
    elif kind == "zero_pairs":
        for i in range(4):
            x=300+i*135
            d.ellipse((x-42,330,x+42,414),fill="#E98A8A",outline=INK,width=3); label(d,(x,372),"+",35,INK,True,anchor="mm")
            d.ellipse((x-42,430,x+42,514),fill="#8DBBE8",outline=INK,width=3); label(d,(x,472),"−",35,INK,True,anchor="mm")
        label(d,(540,240),"One positive and one negative make zero",28,BLUE,True,anchor="mm")
        label(d,(540,590),"Adding zero pairs does not change the total",26,INK,True,anchor="mm")
    elif kind == "integer_addition":
        d.line((160,440,920,440),fill=INK,width=6)
        for n in range(-4,5):
            x=540+n*90; d.line((x,420,x,460),fill=INK,width=4); label(d,(x,490),n,24,INK,True,anchor="mm")
        arrow(d,(540,360),(810,360),fill="#39834A",width=8)
        arrow(d,(810,330),(630,330),fill="#D35D6E",width=8)
        label(d,(540,255),"Positive moves right; negative moves left",27,BLUE,True,anchor="mm")
    elif kind == "condensation":
        d.rounded_rectangle((410,320,670,590),radius=28,fill="#BFE4F2",outline=INK,width=5)
        for x,y in [(360,350),(700,390),(380,500),(700,530),(540,270)]:
            d.ellipse((x-13,y-13,x+13,y+13),fill="#6CA9D6",outline=INK,width=2)
        arrow(d,(250,300),(390,360),fill=BLUE,width=6)
        label(d,(540,210),"Water vapour cools and forms liquid droplets",27,BLUE,True,anchor="mm")
        label(d,(540,635),"Droplets form on the outside of the cold glass",23,INK,True,anchor="mm")
    elif kind == "evaporation":
        d.rectangle((250,430,830,520),fill="#BFE4F2",outline=INK,width=4)
        for x in [350,470,590,710]:
            arrow(d,(x,410),(x-25,280),fill=BLUE,width=6)
        d.ellipse((760,170,850,260),fill="#F6C66B",outline=INK,width=3)
        label(d,(540,590),"Heat helps liquid water change into vapour",28,BLUE,True,anchor="mm")
    elif kind == "earthen_pot":
        d.ellipse((350,260,730,650),fill="#C98E5B",outline=INK,width=6)
        d.ellipse((390,300,690,610),fill="#BFE4F2",outline=INK,width=4)
        for x,y in [(330,390),(340,450),(350,510),(730,390),(720,450),(710,510)]:
            arrow(d,(x,y),(x-35 if x<500 else x+35,y-55),fill=BLUE,width=5)
        label(d,(540,205),"A little water seeps out and evaporates",28,BLUE,True,anchor="mm")
        label(d,(540,675),"Evaporation cools the earthen pot",24,INK,True,anchor="mm")
    elif kind == "pole_star":
        pts=[(260,420),(360,300),(490,350),(600,470),(470,540),(340,520),(260,420)]
        for a,b in zip(pts,pts[1:]): d.line((a,b),fill="#8DBBE8",width=6)
        for x,y in pts[:-1]: d.ellipse((x-12,y-12,x+12,y+12),fill="#F6C66B",outline=INK,width=2)
        d.ellipse((850,210,880,240),fill="#F6C66B",outline=INK,width=3)
        arrow(d,(610,470),(850,225),fill="#D35D6E",width=6)
        label(d,(865,180),"POLE STAR",22,BLUE,True,anchor="mm")
        label(d,(430,625),"Use the pointer stars to find the Pole Star",25,INK,True,anchor="mm")
    elif kind == "day_night":
        d.ellipse((300,220,780,700),fill="#547DB5",outline=INK,width=5)
        d.pieslice((300,220,780,700),90,270,fill="#F6C66B",outline=INK,width=3)
        d.ellipse((500,420,580,500),fill="#8DBBE8",outline=INK,width=3)
        arrow(d,(520,210),(700,210),fill=BLUE,width=7)
        label(d,(410,455),"DAY",26,INK,True,anchor="mm"); label(d,(670,455),"NIGHT",26,"#FFFFFF",True,anchor="mm")
        label(d,(540,180),"Earth rotates on its axis",28,BLUE,True,anchor="mm")
    elif kind == "compass":
        d.ellipse((340,220,740,620),fill="#F2F5F7",outline=INK,width=7)
        d.line((540,270,540,570),fill=INK,width=4); d.line((390,420,690,420),fill=INK,width=4)
        d.polygon([(540,285),(505,430),(540,405),(575,430)],fill="#D35D6E",outline=INK)
        d.polygon([(540,555),(505,410),(540,435),(575,410)],fill="#8DBBE8",outline=INK)
        label(d,(540,190),"N",32,BLUE,True,anchor="mm"); label(d,(540,650),"S",32,BLUE,True,anchor="mm")
        label(d,(760,420),"E",26,INK,True); label(d,(300,420),"W",26,INK,True)
    elif kind == "magnet_poles":
        for y,left,right,desc in [(320,"N","N","LIKE POLES REPEL"),(520,"N","S","UNLIKE POLES ATTRACT")]:
            for x,pole in [(260,left),(650,right)]:
                d.rounded_rectangle((x,y-45,x+170,y+45),radius=16,fill="#E98A8A" if pole=="N" else "#8DBBE8",outline=INK,width=4)
                label(d,(x+85,y),pole,35,INK,True,anchor="mm")
            if left==right: arrow(d,(450,y),(370,y),fill="#D35D6E",width=7); arrow(d,(630,y),(550,y),fill="#D35D6E",width=7)
            else: arrow(d,(440,y),(570,y),fill="#39834A",width=7)
            label(d,(540,y+75),desc,23,BLUE,True,anchor="mm")
    elif kind == "handpicking":
        d.rounded_rectangle((230,300,850,560),radius=30,fill="#E8C48B",outline=INK,width=5)
        for x,y in [(330,370),(470,450),(620,350),(740,470),(560,500)]:
            d.ellipse((x-18,y-12,x+18,y+12),fill="#6B6257",outline=INK,width=2)
        label(d,(540,220),"Remove visible unwanted stones by hand",28,BLUE,True,anchor="mm")
        label(d,(540,610),"GRAINS + STONES",25,INK,True,anchor="mm")
    elif kind == "winnowing":
        d.polygon([(260,280),(610,370),(570,440),(220,350)],fill="#D8B477",outline=INK)
        for i in range(9):
            x=650+i*24; y=330+(i%3)*32
            d.ellipse((x,y,x+12,y+12),fill="#E8C48B",outline=INK)
        arrow(d,(620,340),(900,260),fill=BLUE,width=8)
        for i in range(6):
            x=450+i*22; d.ellipse((x,500+(i%2)*18,x+14,514+(i%2)*18),fill="#C99A4A",outline=INK)
        label(d,(780,210),"LIGHT HUSK",23,BLUE,True,anchor="mm")
        label(d,(430,590),"HEAVIER GRAINS FALL NEARBY",22,INK,True,anchor="mm")
    elif kind == "salt_evaporation":
        d.rounded_rectangle((300,330,780,500),radius=24,fill="#BFE4F2",outline=INK,width=5)
        for x in [390,500,610,700]: arrow(d,(x,310),(x-20,220),fill=BLUE,width=5)
        d.rectangle((350,520,730,570),fill="#F6C66B",outline=INK,width=3)
        label(d,(540,200),"Water evaporates; salt remains",29,BLUE,True,anchor="mm")
        label(d,(540,630),"SALT CRYSTALS",24,INK,True,anchor="mm")
    elif kind == "magnetic_separation":
        d.rounded_rectangle((250,260,830,380),radius=22,fill="#8DBBE8",outline=INK,width=5)
        for x in [350,450,550,650,750]:
            d.line((x,430,x+25,455),fill="#9B7545",width=8)
        d.rounded_rectangle((400,190,680,250),radius=18,fill="#E98A8A",outline=INK,width=4)
        label(d,(540,220),"MAGNET",22,INK,True,anchor="mm")
        for x in [430,500,570,640]: arrow(d,(x,410),(x,275),fill="#D35D6E",width=5)
        label(d,(540,550),"Iron is attracted; other material stays",27,BLUE,True,anchor="mm")
    elif kind == "windmill":
        d.line((540,400,540,640),fill=INK,width=12)
        d.ellipse((500,360,580,440),fill="#F6C66B",outline=INK,width=4)
        for a in [0,90,180,270]:
            rad=math.radians(a); x=540+180*math.cos(rad); y=400+180*math.sin(rad)
            d.polygon([(540,400),(x-35*math.sin(rad),y+35*math.cos(rad)),(x+35*math.sin(rad),y-35*math.cos(rad))],fill="#8DBBE8",outline=INK)
        arrow(d,(180,320),(340,320),fill=BLUE,width=8); arrow(d,(180,390),(340,390),fill=BLUE,width=8)
        label(d,(540,200),"Moving air turns the pinwheel blades",28,BLUE,True,anchor="mm")
    elif kind == "fresh_water":
        cards=[(130,280,"RIVERS & LAKES","#BFE4F2"),(570,280,"ICE & SNOW","#DCE7F4"),(130,450,"GROUNDWATER","#D8B477"),(570,450,"WATER IN SOIL","#EAF4E4")]
        for x,y,name,col in cards:
            d.rounded_rectangle((x,y,x+370,y+115),radius=20,fill=col,outline=INK,width=4)
            label(d,(x+185,y+57),name,24,INK,True,anchor="mm")
        label(d,(540,205),"Fresh water is found in rivers, lakes, ice and underground",25,BLUE,True,anchor="mm")
    elif kind == "soil_formation":
        d.rectangle((230,300,850,620),fill="#C99A6B",outline=INK,width=5)
        d.rectangle((230,300,850,390),fill="#8BCB83",outline=INK,width=3)
        for x,y,r in [(330,460,22),(450,520,15),(600,440,26),(740,550,20),(520,350,12)]:
            d.ellipse((x-r,y-r,x+r,y+r),fill="#8C8174",outline=INK,width=2)
        arrow(d,(300,220),(390,290),fill="#E39A35",width=6); arrow(d,(540,220),(540,290),fill=BLUE,width=6)
        label(d,(540,190),"Rocks break down slowly into soil",28,BLUE,True,anchor="mm")
        label(d,(540,660),"Rock pieces + water + air + living things",23,INK,True,anchor="mm")
    elif kind == "vehicle_fuels":
        cards=[("CAR","PETROL"),("BUS","DIESEL"),("AUTO","CNG"),("E-BUS","ELECTRICITY")]
        for i,(vehicle,fuel) in enumerate(cards):
            x=130+(i%2)*440; y=260+(i//2)*190
            d.rounded_rectangle((x,y,x+380,y+130),radius=20,fill=PALETTE[i%4],outline=INK,width=4)
            label(d,(x+190,y+42),vehicle,27,INK,True,anchor="mm")
            label(d,(x+190,y+90),fuel,24,BLUE,True,anchor="mm")
    elif kind == "digital_thermometer":
        d.rounded_rectangle((400,300,680,430),radius=24,fill="#F2F5F7",outline=INK,width=5)
        label(d,(540,365),"37.0 °C",48,BLUE,True,anchor="mm")
        label(d,(540,230),"Example: normal body temperature",28,BLUE,True,anchor="mm")
        label(d,(540,540),"Hold safely; clean before and after use",25,INK,True,anchor="mm")
    elif kind == "lab_thermometer":
        d.rounded_rectangle((500,210,580,590),radius=35,fill="#F2F5F7",outline=INK,width=5)
        d.ellipse((480,545,600,665),fill="#E46B5D",outline=INK,width=4)
        d.rectangle((525,360,555,600),fill="#E46B5D")
        for i,t in enumerate(["0","20","40","60","80","100"]):
            y=550-i*55; d.line((580,y,650,y),fill=INK,width=3); label(d,(670,y-14),t,22,INK)
        label(d,(260,300),"SCALE",24,BLUE,True); label(d,(260,550),"BULB",24,BLUE,True)
        label(d,(540,185),"Read the liquid level against the scale",27,BLUE,True,anchor="mm")
    elif kind == "thermometer_setup":
        d.rectangle((300,430,780,620),fill="#BFE4F2",outline=INK,width=5)
        d.rounded_rectangle((520,230,560,500),radius=18,fill="#F2F5F7",outline=INK,width=4)
        d.ellipse((510,470,570,530),fill="#E46B5D",outline=INK,width=3)
        label(d,(540,200),"Keep the thermometer upright",27,BLUE,True,anchor="mm")
        label(d,(540,660),"Bulb stays in water, away from the sides and bottom",22,INK,True,anchor="mm")
    elif kind == "melting_plateau":
        pts=[(180,520),(350,390),(560,390),(850,220)]
        d.line(pts,fill=BLUE,width=10,joint="curve")
        for x,y in pts: d.ellipse((x-10,y-10,x+10,y+10),fill=INK)
        label(d,(300,570),"ICE WARMS",23,INK,True); label(d,(450,350),"MELTING: TEMP STAYS LEVEL",22,BLUE,True,anchor="mm")
        label(d,(800,190),"WATER WARMS",22,INK,True,anchor="mm")
    elif kind == "temperature_scales":
        for x,name,marks in [(280,"CELSIUS",["0°","20°","40°"]),(540,"FAHRENHEIT",["32°","68°","104°"]),(800,"KELVIN",["273 K","293 K","313 K"])]:
            d.line((x,280,x,570),fill=INK,width=8)
            for i,t in enumerate(marks):
                y=300+i*115; d.line((x-22,y,x+22,y),fill=INK,width=4); label(d,(x+35,y-15),t,20,INK)
            label(d,(x,620),name,21,BLUE,True,anchor="mm")

    elif kind == "forest_products":
        cards=[(150,270,"FRUITS","#F6C66B"),(570,270,"WOOD","#C99A6B"),(150,450,"MEDICINAL PLANTS","#9ACB87"),(570,450,"HONEY","#FFF0D9")]
        for x,y,name,col in cards:
            d.rounded_rectangle((x,y,x+360,y+120),radius=22,fill=col,outline=INK,width=4)
            label(d,(x+180,y+60),name,24,INK,True,anchor="mm")
        label(d,(540,205),"Forests provide useful products and habitats",28,BLUE,True,anchor="mm")
    else:
        raise ValueError(f"Unsupported diagram type: {kind}")

def render_panel(panel, out_path, panel_no, panel_total):
    image=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(image)
    d.rounded_rectangle((24,24,W-24,H-24),radius=30,fill="#FFFFFF",outline="#DCE5EA",width=3)
    d.rounded_rectangle((52,48,W-52,158),radius=22,fill=PALETTE[(panel_no-1)%4])
    heading=str(panel.get("heading","")).strip()
    if not heading: raise ValueError("Panel heading is required")
    words=heading.split(); lines=[]; current=""
    for word in words:
        candidate=(current+" "+word).strip()
        if d.textbbox((0,0),candidate,font=font(31,True))[2] > 900 and current:
            lines.append(current); current=word
        else: current=candidate
    if current: lines.append(current)
    if len(lines)>2: raise ValueError("Panel heading is too long; shorten it")
    for i,line in enumerate(lines): label(d,(82,64+i*39),line,31,INK,True)
    kind=panel.get("diagram")
    if kind: diagram(d,kind,panel)
    else:
        lines=panel.get("lines",[])
        if not isinstance(lines,list) or not lines: raise ValueError("Panel needs a diagram or reviewed lines")
        y=205
        for i,item in enumerate(lines):
            f=font(31,i==0); d.ellipse((82,y+7,112,y+37),fill=BLUE); label(d,(97,y+22),i+1,19,"#FFFFFF",True,anchor="mm")
            words=str(item).split(); current=""
            for word in words:
                candidate=(current+" "+word).strip()
                if d.textbbox((0,0),candidate,font=f)[2] > 820 and current:
                    label(d,(140,y),current,31,INK,i==0); y+=44; current=word
                else: current=candidate
            if current: label(d,(140,y),current,31,INK,i==0); y+=44
            y+=26
            if y>H-100: raise ValueError("Panel text overflows; shorten or split it")
    if panel_total>1: label(d,(W-110,H-75),f"{panel_no}/{panel_total}",22,BLUE,True,anchor="mm")
    image.save(out_path,"PNG",optimize=True); return out_path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--out",default="assets/lesson-images/generated")
    args=ap.parse_args(); manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    items=manifest.get("images",[])
    if not isinstance(items,list) or not items: raise SystemExit("Manifest needs a non-empty images array")
    root=Path(args.out); outputs=[]; seen=set()
    for item in items:
        required=("lesson_id","module_key","step_ids","title","alt_text","layout","panels")
        missing=[k for k in required if k not in item]
        if missing: raise ValueError(f"Missing {missing} in {item.get('title')}")
        if item["layout"] not in ("single","pair"): raise ValueError("layout must be single or pair")
        if not isinstance(item["step_ids"],list) or not item["step_ids"]: raise ValueError("step_ids must be a non-empty list")
        expected=1 if item["layout"]=="single" else 2
        if len(item["panels"])!=expected: raise ValueError(f"{item['layout']} needs exactly {expected} panels")
        key=(item["lesson_id"],item["module_key"],tuple(item["step_ids"]))
        if key in seen: raise ValueError(f"Duplicate mapping: {key}")
        seen.add(key); slug=re.sub(r"[^a-z0-9]+","-",item["title"].lower()).strip("-")[:64]
        folder=root/item["lesson_id"]/item["module_key"]; folder.mkdir(parents=True,exist_ok=True); paths=[]
        for n,panel in enumerate(item["panels"],1):
            name=f"{slug}-panel-{n}.png" if expected==2 else f"{slug}.png"
            paths.append(str(render_panel(panel,folder/name,n,expected)))
        outputs.append({"lesson_id":item["lesson_id"],"module_key":item["module_key"],"step_ids":item["step_ids"],
                        "layout":item["layout"],"title":item["title"],"alt_text":item["alt_text"],"files":paths})
    (root/"rendered-manifest.json").write_text(json.dumps({"images":outputs},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"rendered":len(outputs),"files":sum(len(x["files"]) for x in outputs),"manifest":str(root/"rendered-manifest.json")},indent=2))

if __name__=="__main__": main()
