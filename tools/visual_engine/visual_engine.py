#!/usr/bin/env python3
"""Source-gated, deterministic educational visual generator for PadippuPal."""
from __future__ import annotations
import argparse, html, json, re, sys, uuid
from pathlib import Path

VERSION = "0.2.0"
ALLOWED_EVIDENCE = {"source_verified", "concept_source_verified"}
INK, BLUE, PALE_BLUE, GREEN, ORANGE, GREY = "#25364A", "#4C83D6", "#E7F0FF", "#3C9B78", "#E7A34B", "#64748B"

class VisualError(ValueError):
    pass

def esc(value):
    return html.escape(str(value), quote=True)

def classify(subject, topic, chapter):
    text = f"{subject} {chapter} {topic}".lower()
    if "math" in subject.lower():
        if any(k in text for k in ("pattern", "sequence", "repeating")): return "math_patterns"
        if "fraction" in text: return "math_fractions"
        if "angle" in text: return "math_angles"
        if "symmetry" in text: return "math_symmetry"
    if "science" in subject.lower():
        if any(k in text for k in ("states of water", "state of water", "solid liquid gas", "particle state")): return "science_states_water"
        if "water cycle" in text: return "science_water_cycle"
        if "magnet" in text: return "science_magnets"
        if any(k in text for k in ("jigsaw", "knowledge grows", "new discovery")): return "science_jigsaw"
        if any(k in text for k in ("pen stops writing", "pen inquiry", "check the refill", "ink is empty")): return "science_pen_inquiry"
        if any(k in text for k in ("scientific method", "scientific inquiry", "observe ask guess test")): return "science_inquiry"
        if any(k in text for k in ("paper", "metal key", "plastic ruler", "rubber eraser", "everyday objects")): return "science_everyday_objects"
        if any(k in text for k in ("daily life", "everyday problem", "cooking", "bicycle tyre", "light bulb")): return "science_daily_life"
        if any(k in text for k in ("curiosity", "ask why", "flower bloom", "stars shine", "ask questions")): return "science_curiosity"
    raise VisualError(f"No topic-specific renderer for {subject!r} / {chapter!r} / {topic!r}; refusing generic fallback.")

def validate(a):
    if not all([a.subject.strip(), a.chapter.strip(), a.topic.strip(), a.medium.strip(), a.source_id.strip()]):
        raise VisualError("Subject, chapter, topic, medium and source ID are required.")
    if a.source_page < 1: raise VisualError("--source-page must be positive.")
    if a.evidence_status not in ALLOWED_EVIDENCE:
        raise VisualError("Evidence is not approved for learner-facing output. Review the source first.")

def tile(x, y, shape, color, n):
    mark = (f'<circle cx="{x}" cy="{y}" r="25" fill="{color}" stroke="{INK}" stroke-width="2"/>' if shape == "circle"
            else f'<path d="M{x} {y-27} L{x-27} {y+23} L{x+27} {y+23} Z" fill="{color}" stroke="{INK}" stroke-width="2"/>')
    return mark + f'<text x="{x}" y="{y+45}" text-anchor="middle" font-size="12" fill="{INK}">{n}</text>'

def svg(a, family):
    title, subtitle = esc(a.topic), esc(f"{a.chapter} • {a.subject} • {a.medium}")
    meta = esc(json.dumps({"subject":a.subject,"chapter":a.chapter,"topic":a.topic,"medium":a.medium,
        "source_id":a.source_id,"source_page":a.source_page,"evidence_status":a.evidence_status,"renderer_version":VERSION}, ensure_ascii=False))
    start = f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="340" viewBox="0 0 720 340" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">{subtitle}; source {esc(a.source_id)}, page {a.source_page}</desc><metadata>{meta}</metadata><rect width="720" height="340" rx="16" fill="#FFFFFF"/><text x="28" y="38" font-family="sans-serif" font-size="21" font-weight="700" fill="{INK}">{title}</text><text x="28" y="61" font-family="sans-serif" font-size="12" fill="{GREY}">{subtitle}</text>'
    if family == "math_patterns":
        body = '<text x="28" y="100" font-size="15" fill="'+INK+'">Find what repeats</text>'
        body += tile(75,160,"circle",BLUE,"1")+tile(195,160,"triangle",ORANGE,"2")+tile(315,160,"circle",BLUE,"3")+tile(435,160,"triangle",ORANGE,"4")+tile(555,160,"circle",BLUE,"5")
        body += f'<text x="28" y="265" font-size="14" fill="{INK}">Circle, triangle, circle, triangle…</text><text x="28" y="290" font-size="12" fill="{GREY}">Illustrative pattern; replace with the exact cited textbook example before approval.</text>'
    elif family == "math_fractions":
        body = f'<text x="28" y="105" font-size="15" fill="{INK}">One whole split into four equal parts</text>'
        for i in range(4):
            body += f'<rect x="{70+i*140}" y="135" width="140" height="72" fill="{BLUE if i==0 else PALE_BLUE}" stroke="{INK}" stroke-width="2"/>'
        body += f'<text x="70" y="245" font-size="21" font-weight="700" fill="{INK}">1 / 4</text><text x="150" y="245" font-size="14" fill="{GREY}">One shaded part out of four equal parts</text>'
    elif family == "math_angles":
        body = f'<text x="28" y="105" font-size="15" fill="{INK}">Two rays share a common endpoint.</text><circle cx="250" cy="230" r="5" fill="#C65353"/><path d="M250 230 L490 230 M250 230 L420 125" stroke="{INK}" stroke-width="4" stroke-linecap="round"/><path d="M320 230 A70 70 0 0 0 308 190" fill="none" stroke="{BLUE}" stroke-width="4"/><text x="260" y="255" font-size="13" fill="#C65353">Common endpoint</text><text x="360" y="165" font-size="13" fill="{BLUE}">Angle</text><text x="28" y="300" font-size="12" fill="{GREY}">Schematic only; do not infer a numerical measure.</text>'
    elif family == "math_symmetry":
        body = f'<text x="28" y="105" font-size="15" fill="{INK}">A line of symmetry divides a shape into matching halves.</text><path d="M220 135 L295 185 L270 270 L170 270 L145 185 Z" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="3"/><path d="M220 135 V285" stroke="#C65353" stroke-width="2.5" stroke-dasharray="7 6"/><text x="330" y="200" font-size="14" fill="{INK}">Compare both sides</text><text x="330" y="225" font-size="13" fill="{GREY}">Dashed line shows the proposed mirror line.</text>'
    elif family == "science_states_water":
        body = f'<text x="28" y="100" font-size="15" fill="{INK}">Particle model (schematic, not to scale)</text>'
        for x, label, points in [(35,"Solid",[(.2,.2),(.5,.2),(.8,.2),(.2,.5),(.5,.5),(.8,.5),(.2,.8),(.5,.8),(.8,.8)]),(258,"Liquid",[(.2,.2),(.45,.25),(.7,.2),(.3,.5),(.6,.45),(.8,.55),(.2,.8),(.5,.75),(.75,.8)]),(481,"Gas",[(.15,.2),(.8,.18),(.45,.4),(.22,.7),(.82,.8),(.55,.85)])]:
            body += f'<rect x="{x}" y="120" width="205" height="120" rx="8" fill="#F7F9FC" stroke="{INK}" stroke-width="2"/>'
            for px,py in points: body += f'<circle cx="{x+15+px*175:.1f}" cy="{120+15+py*90:.1f}" r="6" fill="{BLUE}" stroke="{INK}"/>'
            body += f'<text x="{x+102}" y="265" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}">{label}</text>'
        body += f'<text x="35" y="295" font-size="12" fill="{GREY}">Packed and ordered • Close and mobile • Far apart</text>'
    elif family == "science_water_cycle":
        body = f'<circle cx="110" cy="150" r="25" fill="#FFF0D9" stroke="{ORANGE}" stroke-width="3"/><text x="75" y="193" font-size="12" fill="{INK}">Sun warms water</text><path d="M150 150 Q210 110 255 150" fill="none" stroke="{BLUE}" stroke-width="3"/><path d="M245 140 L257 150 L245 160" fill="none" stroke="{BLUE}" stroke-width="3"/><path d="M275 135 Q290 110 310 132 Q340 115 355 140 Q375 142 370 160 H275 Q260 151 275 135Z" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="2"/><text x="270" y="185" font-size="12" fill="{INK}">Vapour cools</text><path d="M390 165 Q430 190 450 220" fill="none" stroke="{BLUE}" stroke-width="3"/><path d="M440 211 L451 222 L455 207" fill="none" stroke="{BLUE}" stroke-width="3"/><path d="M425 245 Q500 210 575 245 Q615 255 650 245 V285 H425Z" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="2"/><text x="465" y="275" font-size="12" fill="{INK}">Water returns</text><text x="28" y="315" font-size="11" fill="{GREY}">Simplified cycle; confirm all stages against source.</text>'
    elif family == "science_magnets":
        body = f'<text x="28" y="105" font-size="15" fill="{INK}">Test objects with a magnet</text><rect x="55" y="145" width="170" height="55" rx="9" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="2"/><rect x="55" y="145" width="85" height="55" rx="8" fill="#C65353"/><text x="88" y="179" font-size="18" font-weight="700" fill="white">N</text><text x="174" y="179" font-size="18" font-weight="700" fill="{INK}">S</text><path d="M245 171 H300" stroke="{GREEN}" stroke-width="3"/><path d="M290 161 L302 171 L290 181" fill="none" stroke="{GREEN}" stroke-width="3"/><circle cx="355" cy="170" r="18" fill="#FFF0D9" stroke="{ORANGE}" stroke-width="2"/><rect x="410" y="154" width="42" height="32" rx="4" fill="#E4F5ED" stroke="{GREEN}" stroke-width="2"/><text x="310" y="220" font-size="12" fill="{INK}">Test one object at a time</text><text x="28" y="285" font-size="12" fill="{GREY}">Classify only after source-supported evidence.</text>'
    elif family in {"science_jigsaw", "science_curiosity", "science_pen_inquiry", "science_inquiry", "science_daily_life", "science_everyday_objects"}:
        labels = {
            "science_jigsaw": ["What we know", "New discovery", "New questions"],
            "science_curiosity": ["Notice", "Ask why", "Explore"],
            "science_pen_inquiry": ["Notice problem", "Make a guess", "Test refill"],
            "science_inquiry": ["Observe", "Ask", "Guess", "Test", "Review"],
            "science_daily_life": ["Daily problem", "Suggest", "Test"],
            "science_everyday_objects": ["Paper", "Metal key", "Plastic ruler", "Eraser"],
        }[family]
        count = len(labels)
        box_w = min(125, 620 / count)
        left = (720 - (count * box_w + (count - 1) * 12)) / 2
        for i, label in enumerate(labels):
            x = left + i * (box_w + 12)
            body += f'<rect x="{x:.1f}" y="125" width="{box_w:.1f}" height="72" rx="10" fill="{PALE_BLUE if i % 2 == 0 else "#E4F5ED"}" stroke="{BLUE if i % 2 == 0 else GREEN}" stroke-width="2"/><text x="{x+box_w/2:.1f}" y="165" text-anchor="middle" font-size="13" fill="{INK}">{esc(label)}</text>'
            if i < count - 1:
                body += f'<path d="M{x+box_w+1:.1f} 161 H{x+box_w+11:.1f}" stroke="{ORANGE}" stroke-width="3"/><path d="M{x+box_w+5:.1f} 155 L{x+box_w+11:.1f} 161 L{x+box_w+5:.1f} 167" fill="none" stroke="{ORANGE}" stroke-width="2"/>'
        body += f'<text x="28" y="270" font-size="12" fill="{GREY}">Original schematic based on the named topic; teacher source review is still required.</text>'
    return start + body + "</svg>\n"

def excalidraw(a, family):
    elements=[]
    for i, text in enumerate([a.topic, f"{a.subject} — {a.chapter}", f"Source: {a.source_id}, page {a.source_page}", f"Renderer: {family}; review before teaching"]):
        elements.append({"id":uuid.uuid4().hex[:20],"type":"text","x":40,"y":35+i*55,"width":640,"height":32,"angle":0,"strokeColor":INK,"backgroundColor":"transparent","fillStyle":"hachure","strokeWidth":1,"strokeStyle":"solid","roughness":1,"opacity":100,"groupIds":[],"frameId":None,"roundness":None,"seed":i+17,"version":1,"versionNonce":i+41,"isDeleted":False,"boundElements":None,"updated":0,"link":None,"locked":False,"text":text,"fontSize":24 if i==0 else 16,"fontFamily":1,"textAlign":"left","verticalAlign":"top","baseline":24,"containerId":None,"originalText":text,"autoResize":True})
    return json.dumps({"type":"excalidraw","version":2,"source":"PadippuPal Visual Engine","elements":elements,"appState":{"viewBackgroundColor":"#ffffff","gridSize":None,"zoom":{"value":1},"scrollX":0,"scrollY":0},"files":{}},ensure_ascii=False,indent=2)

def manim_source(a, family):
    return f'''from manim import *

class PadippuPalTopicVisual(Scene):
    """Starter source for {a.subject} / {a.chapter} / {a.topic}.
    Source: {a.source_id}, page {a.source_page}; review before learner use.
    """
    def construct(self):
        title = Text({a.topic!r}, font_size=30)
        subtitle = Text({(a.chapter + " • " + a.subject)!r}, font_size=18, color=BLUE)
        self.play(Write(title), FadeIn(subtitle))
        self.wait(0.5)
        note = Text("Source-checked animation steps required", font_size=20, color=YELLOW)
        self.play(Write(note))
        self.wait(1)
'''

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    r=sub.add_parser("render")
    for name in ("subject","chapter","topic","medium","source-id","out"): r.add_argument("--"+name,required=True)
    r.add_argument("--source-page",type=int,required=True)
    r.add_argument("--evidence-status",choices=["source_verified","concept_source_verified","needs_review","text_only_inference"],required=True)
    r.add_argument("--format",choices=["svg","excalidraw","manim"],default="svg")
    a=p.parse_args()
    if a.cmd=="list":
        print("Mathematics: repeating patterns, fractions, angles, symmetry\nScience: states of water, water cycle, magnets\nUnsupported topics fail closed."); return 0
    try:
        validate(a); family=classify(a.subject,a.topic,a.chapter)
        content={"svg":svg,"excalidraw":excalidraw,"manim":manim_source}[a.format](a,family)
        out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(content,encoding="utf-8")
        print(json.dumps({"ok":True,"family":family,"format":a.format,"output":str(out),"renderer_version":VERSION,"source_id":a.source_id,"source_page":a.source_page,"evidence_status":a.evidence_status}))
        return 0
    except (VisualError,OSError) as e:
        print(f"visual-engine: {e}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
