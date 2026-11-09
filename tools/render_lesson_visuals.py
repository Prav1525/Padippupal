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
    elif kind == "area_perimeter":
        x0,y0,x1,y1=180,220,850,560
        d.rectangle((x0,y0,x1,y1),fill="#E8F4F8",outline=INK,width=8)
        for x in range(x0+67,x1,67): d.line((x,y0,x,y1),fill="#A7C9D8",width=2)
        for y in range(y0+68,y1,68): d.line((x0,y,x1,y),fill="#A7C9D8",width=2)
        label(d,(515,590),data.get("length","6 units"),30,BLUE,True,anchor="mm")
        label(d,(110,390),data.get("width","3 units"),28,BLUE,True,anchor="mm")
        label(d,(515,380),"AREA = inside",38,INK,True,anchor="mm")
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
