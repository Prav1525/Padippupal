#!/usr/bin/env python3
"""Create a draft, source-review-gated inline drawing sample for CBSE Class 6 Science Chapter 12.

This tool writes original SVG and Excalidraw-compatible storyboard files only.
It never writes to Neon or activates learner-facing assets. Review against the official
NCERT chapter before use; all generated assets remain inactive and need_review.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import uuid

CHAPTER = "Beyond Earth"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/fecu112.pdf"
VERSION = "0.1.0"
INK = "#24324A"
BLUE = "#3978D4"
SKY = "#DCEEFF"
MINT = "#DDF5E7"
YELLOW = "#FFE69A"
PINK = "#FFDCEC"
LAVENDER = "#E8E1FF"
GREY = "#65748B"
GREEN = "#2F8F67"
DARK = "#17243B"
WHITE = "#FFFFFF"

MODULES = [
    {
        "id": "earth-moon-sun",
        "topic": "Earth, Moon and Sun",
        "narration": "The Sun is a star. Earth moves around the Sun, and the Moon moves around Earth. This sketch is not to scale.",
        "caption": "Sun → Earth’s orbit → Moon’s orbit around Earth",
        "prompt": "Trace the paths with your finger: Earth around the Sun, and Moon around Earth.",
        "kind": "orbits",
    },
    {
        "id": "day-and-night",
        "topic": "Day and night",
        "narration": "Earth rotates. The side facing the Sun has daylight, while the side turned away has night.",
        "caption": "Earth’s rotation causes day and night.",
        "prompt": "Point to the day side, then the night side. What changes as Earth rotates?",
        "kind": "day_night",
    },
    {
        "id": "phases-of-the-moon",
        "topic": "Phases of the Moon",
        "narration": "The Moon does not make its own light. Sunlight illuminates half of it, and as the Moon moves around Earth, we see different portions of that lit half.",
        "caption": "The Moon’s changing appearance is called its phases.",
        "prompt": "Compare the new, quarter and full Moon sketches. Which part is lit by the Sun?",
        "kind": "phases",
    },
]

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)

def svg_start(module: dict) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="360" viewBox="0 0 760 360" role="img" aria-labelledby="title desc">
<title id="title">{esc(module["topic"])}</title>
<desc id="desc">Original hand-drawn-style draft for inline teaching; review against the cited NCERT source before learner use.</desc>
<rect width="760" height="360" rx="22" fill="#FFFFFF"/>
<path d="M24 72 Q21 65 33 64 L720 64 Q735 64 732 76" fill="none" stroke="{BLUE}" stroke-width="2.5" stroke-linecap="round"/>
<text x="30" y="42" font-family="Trebuchet MS, sans-serif" font-size="25" font-weight="700" fill="{INK}">{esc(module["topic"])}</text>
<text x="31" y="92" font-family="Trebuchet MS, sans-serif" font-size="14" fill="{GREY}">Let’s draw it together ✎</text>'''

def render_svg(module: dict) -> str:
    body = ""
    if module["kind"] == "orbits":
        body = f'''
<ellipse cx="365" cy="220" rx="245" ry="105" fill="none" stroke="{BLUE}" stroke-width="3" stroke-dasharray="9 8" transform="rotate(-7 365 220)"/>
<circle cx="365" cy="220" r="37" fill="{YELLOW}" stroke="#D6A52C" stroke-width="3"/>
<path d="M344 194 Q365 180 383 197 M335 220 Q352 230 366 213 M370 246 Q389 235 394 216" fill="none" stroke="#D6A52C" stroke-width="2.5" stroke-linecap="round"/>
<text x="365" y="277" text-anchor="middle" font-size="17" font-weight="700" fill="{INK}">Sun</text>
<ellipse cx="365" cy="220" rx="108" ry="58" fill="none" stroke="{GREY}" stroke-width="2.5" stroke-dasharray="5 7" transform="rotate(25 365 220)"/>
<circle cx="473" cy="220" r="22" fill="{SKY}" stroke="{BLUE}" stroke-width="3"/>
<path d="M461 215 Q468 205 475 216 L484 222 L476 232 L466 229Z" fill="{MINT}" stroke="#55A879" stroke-width="1.5"/>
<text x="473" y="264" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">Earth</text>
<ellipse cx="473" cy="220" rx="48" ry="26" fill="none" stroke="{GREY}" stroke-width="2" stroke-dasharray="4 5"/>
<circle cx="518" cy="211" r="9" fill="{LAVENDER}" stroke="{BLUE}" stroke-width="2.5"/>
<text x="552" y="209" font-size="15" font-weight="700" fill="{INK}">Moon</text>
<path d="M542 214 L529 212" stroke="{BLUE}" stroke-width="2.5" stroke-linecap="round"/>
<rect x="48" y="126" width="200" height="52" rx="15" fill="{PINK}" stroke="#E68CB5" stroke-width="2"/>
<text x="148" y="148" text-anchor="middle" font-size="15" font-weight="700" fill="{INK}">Two different paths</text>
<text x="148" y="166" text-anchor="middle" font-size="12" fill="{INK}">Not drawn to scale</text>
<path d="M250 152 Q285 158 303 179" fill="none" stroke="#E68CB5" stroke-width="2.5" stroke-linecap="round"/>
<text x="40" y="324" font-size="14" fill="{INK}">Teacher prompt: Which object goes around Earth?</text>'''
    elif module["kind"] == "day_night":
        body = f'''
<circle cx="115" cy="200" r="42" fill="{YELLOW}" stroke="#D6A52C" stroke-width="3"/>
<g stroke="#E7B83D" stroke-width="3" stroke-linecap="round">
<path d="M115 145 V132 M115 255 V268 M60 200 H47 M170 200 H183 M76 161 L66 151 M154 239 L164 249 M154 161 L164 151 M76 239 L66 249"/>
</g>
<text x="115" y="271" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">Sun</text>
<g stroke="#E7B83D" stroke-width="2.5" stroke-linecap="round"><path d="M177 180 L246 180"/><path d="M177 200 L246 200"/><path d="M177 220 L246 220"/></g>
<path d="M237 172 L249 180 L237 188 M237 192 L249 200 L237 208 M237 212 L249 220 L237 228" fill="none" stroke="#E7B83D" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="440" cy="200" r="94" fill="{YELLOW}" stroke="{BLUE}" stroke-width="3"/>
<path d="M440 106 A94 94 0 0 1 440 294 Z" fill="#33445F"/>
<path d="M440 106 A94 94 0 0 0 440 294" fill="none" stroke="{BLUE}" stroke-width="3"/>
<path d="M440 95 L454 118 L440 112 L426 118 Z" fill="{PINK}" stroke="{BLUE}" stroke-width="2"/>
<path d="M440 305 L454 282 L440 288 L426 282 Z" fill="{PINK}" stroke="{BLUE}" stroke-width="2"/>
<text x="390" y="192" text-anchor="middle" font-size="17" font-weight="700" fill="{INK}">DAY</text>
<text x="490" y="192" text-anchor="middle" font-size="16" font-weight="700" fill="{WHITE}">NIGHT</text>
<text x="440" y="325" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">Earth rotates ↻</text>
<rect x="560" y="142" width="156" height="82" rx="15" fill="{MINT}" stroke="#55A879" stroke-width="2"/>
<text x="638" y="167" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}">Remember</text>
<text x="638" y="188" text-anchor="middle" font-size="12" fill="{INK}">Earth spins;</text>
<text x="638" y="205" text-anchor="middle" font-size="12" fill="{INK}">the Sun appears</text>
<text x="638" y="220" text-anchor="middle" font-size="12" fill="{INK}">to move across sky.</text>
<text x="40" y="324" font-size="14" fill="{INK}">Light reaches one side at a time.</text>'''
    elif module["kind"] == "phases":
        body = f'''
<circle cx="200" cy="210" r="42" fill="{SKY}" stroke="{BLUE}" stroke-width="3"/>
<path d="M181 181 Q199 164 216 182 L223 199 L208 214 L215 233 L191 248 L174 227 L178 207Z" fill="{MINT}" stroke="#55A879" stroke-width="1.5"/>
<text x="200" y="272" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">Earth</text>
<ellipse cx="200" cy="210" rx="137" ry="91" fill="none" stroke="{GREY}" stroke-width="2.5" stroke-dasharray="6 7"/>
<g stroke="#D6A52C" stroke-width="2.5" stroke-linecap="round"><path d="M35 130 L58 142"/><path d="M28 158 L53 163"/><path d="M29 185 L52 184"/></g>
<circle cx="28" cy="210" r="20" fill="{YELLOW}" stroke="#D6A52C" stroke-width="2.5"/>
<text x="28" y="247" text-anchor="middle" font-size="12" fill="{INK}">Sunlight</text>
<circle cx="200" cy="119" r="15" fill="#E8EAF0" stroke="{BLUE}" stroke-width="2.5"/>
<path d="M200 104 A15 15 0 0 1 200 134 Z" fill="#303D55"/>
<text x="200" y="99" text-anchor="middle" font-size="12" fill="{INK}">Quarter</text>
<circle cx="63" cy="210" r="15" fill="#303D55" stroke="{BLUE}" stroke-width="2.5"/>
<text x="63" y="244" text-anchor="middle" font-size="12" fill="{INK}">New</text>
<circle cx="337" cy="210" r="15" fill="#E8EAF0" stroke="{BLUE}" stroke-width="2.5"/>
<text x="337" y="244" text-anchor="middle" font-size="12" fill="{INK}">Full</text>
<rect x="400" y="128" width="310" height="142" rx="18" fill="{LAVENDER}" stroke="#9B8CE0" stroke-width="2"/>
<text x="555" y="158" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">Why does it change?</text>
<text x="422" y="188" font-size="14" fill="{INK}">• The Moon reflects sunlight.</text>
<text x="422" y="213" font-size="14" fill="{INK}">• Half of the Moon is lit.</text>
<text x="422" y="238" font-size="14" fill="{INK}">• We see different portions as</text>
<text x="437" y="257" font-size="14" fill="{INK}">the Moon moves around Earth.</text>
<text x="400" y="307" font-size="12" fill="{GREY}">Simplified teaching sketch; phase positions are schematic.</text>'''
    else:
        raise ValueError(f"Unknown module kind: {module['kind']}")
    return svg_start(module) + body + "</svg>\n"

def element(kind: str, x: float, y: float, width: float, height: float, **kwargs) -> dict:
    base = {
        "id": uuid.uuid4().hex[:20], "type": kind, "x": x, "y": y,
        "width": width, "height": height, "angle": 0,
        "strokeColor": kwargs.pop("strokeColor", INK),
        "backgroundColor": kwargs.pop("backgroundColor", "transparent"),
        "fillStyle": "hachure", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 2, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 3} if kind == "rectangle" else None,
        "seed": int(uuid.uuid4().hex[:7], 16), "version": 1,
        "versionNonce": int(uuid.uuid4().hex[:7], 16), "isDeleted": False,
        "boundElements": None, "updated": 0, "link": None, "locked": False,
    }
    base.update(kwargs)
    return base

def text_element(text: str, x: float, y: float, size: int = 20, color: str = INK) -> dict:
    return element("text", x, y, max(100, len(text) * size * .62), size + 10,
                   strokeColor=color, text=text, fontSize=size, fontFamily=1,
                   textAlign="left", verticalAlign="top", baseline=size,
                   containerId=None, originalText=text, autoResize=True)

def render_excalidraw(module: dict) -> dict:
    e = []
    e.append(text_element(module["topic"], 35, 25, 28))
    e.append(text_element("PadippuPal • teacher-drawn draft • not to scale", 36, 66, 15, GREY))
    if module["kind"] == "orbits":
        e += [
            element("ellipse", 100, 110, 470, 210, strokeColor=BLUE),
            element("ellipse", 260, 175, 180, 90, strokeColor=GREY),
            element("ellipse", 315, 185, 68, 68, strokeColor="#D6A52C", backgroundColor=YELLOW),
            text_element("Sun", 330, 260, 18),
            element("ellipse", 425, 205, 42, 42, strokeColor=BLUE, backgroundColor=SKY),
            text_element("Earth", 414, 250, 16),
            element("ellipse", 464, 204, 18, 18, strokeColor=BLUE, backgroundColor=LAVENDER),
            text_element("Moon", 492, 198, 15),
            text_element("Earth travels around the Sun", 75, 125, 16, BLUE),
            text_element("Moon travels around Earth", 425, 295, 15, GREEN),
        ]
    elif module["kind"] == "day_night":
        e += [
            element("ellipse", 65, 150, 80, 80, strokeColor="#D6A52C", backgroundColor=YELLOW),
            text_element("Sun", 88, 238, 16),
            element("ellipse", 340, 130, 180, 180, strokeColor=BLUE, backgroundColor=YELLOW),
            element("rectangle", 430, 130, 90, 180, strokeColor=DARK, backgroundColor=DARK),
            text_element("DAY", 365, 205, 20),
            text_element("NIGHT", 445, 205, 18, WHITE),
            text_element("Earth rotates", 350, 320, 16, BLUE),
            text_element("Sunlight →", 175, 190, 18, "#D6A52C"),
        ]
    else:
        e += [
            element("ellipse", 160, 145, 180, 180, strokeColor=BLUE, backgroundColor=SKY),
            text_element("Earth", 220, 335, 18),
            element("ellipse", 105, 105, 290, 250, strokeColor=GREY),
            element("ellipse", 238, 98, 30, 30, strokeColor=BLUE, backgroundColor=WHITE),
            text_element("Quarter", 270, 95, 15),
            element("ellipse", 90, 220, 30, 30, strokeColor=BLUE, backgroundColor=DARK),
            text_element("New", 70, 255, 15),
            element("ellipse", 382, 220, 30, 30, strokeColor=BLUE, backgroundColor=WHITE),
            text_element("Full", 415, 225, 15),
            text_element("Different positions show different portions of the lit half", 430, 150, 16, BLUE),
            text_element("Sunlight illuminates half the Moon", 430, 205, 16, GREEN),
        ]
    e.append(text_element("Review against NCERT before learner use • visual remains inactive", 35, 420, 13, GREY))
    return {
        "type": "excalidraw", "version": 2, "source": "PadippuPal Visual Engine",
        "elements": e,
        "appState": {"viewBackgroundColor": WHITE, "gridSize": None, "zoom": {"value": 0.8}, "scrollX": 0, "scrollY": 0},
        "files": {},
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="build/visuals/science-beyond-earth")
    parser.add_argument("--format", choices=("svg", "excalidraw", "both"), default="both")
    args = parser.parse_args()
    out = Path(args.out_dir)
    assets = []
    for module in MODULES:
        record = {
            "module_id": module["id"], "topic": module["topic"], "chapter": CHAPTER,
            "board": "CBSE", "class_level": 6, "subject": "Science",
            "source_url": SOURCE_URL, "source_page_range": "chapter-level locator; verify exact page per module",
            "source_status": "needs_review", "approval_status": "draft",
            "active": False, "database_written": False,
            "render_mode": "inline_below_module", "overlay": False,
            "narration": module["narration"], "caption": module["caption"],
            "teacher_prompt": module["prompt"], "renderer_version": VERSION,
            "asset_paths": {},
        }
        stem = module["id"]
        if args.format in ("svg", "both"):
            path = out / f"{stem}.svg"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_svg(module), encoding="utf-8")
            record["asset_paths"]["svg"] = str(path)
        if args.format in ("excalidraw", "both"):
            path = out / f"{stem}.excalidraw"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(render_excalidraw(module), ensure_ascii=False, indent=2), encoding="utf-8")
            record["asset_paths"]["excalidraw"] = str(path)
        assets.append(record)
    manifest = {
        "chapter": CHAPTER, "board": "CBSE", "class_level": 6, "subject": "Science",
        "source_url": SOURCE_URL, "renderer_version": VERSION,
        "purpose": "One-chapter inline teacher-drawing pilot",
        "rendering_contract": {
            "position": "after_the_explanation_for_each_module",
            "scroll": "normal_document_flow",
            "overlay": False, "separate_window": False,
            "narration_sync": "module_caption_and_teacher_prompt",
        },
        "assets": assets,
        "database_writes": 0,
        "learner_activation": False,
        "review_note": "Draft sample only. Verify all diagrams and wording against official NCERT Chapter 12 before approval or production integration.",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"chapter": CHAPTER, "modules": len(assets), "format": args.format,
                      "output_dir": str(out), "database_writes": 0, "learner_activation": False,
                      "review_required": True}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
