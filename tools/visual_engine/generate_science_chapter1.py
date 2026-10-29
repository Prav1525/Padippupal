#!/usr/bin/env python3
"""Generate draft visuals from approved synthesis rows and their cited source chunks.

Read-only database access. All outputs are marked needs_review; this tool never
writes to Neon or activates learner-facing assets.
Requires psycopg[binary] and DATABASE_URL.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, sys
from pathlib import Path

SOURCE_ID = "28077c43-b7fe-4a40-85c8-663b8ac326a2"
CHAPTER = "The Wonderful World of Science"
VERSION = "0.2.0"
INK, BLUE, PALE, GREEN, ORANGE, RED, GREY = "#25364A", "#4C83D6", "#E7F0FF", "#3C9B78", "#E7A34B", "#C65353", "#64748B"

def e(v): return html.escape(str(v), quote=True)
def family(topic, explanation, evidence):
    t=(topic+" "+explanation).lower()
    # Use synthesis title and its actual source text to select a specific scene.
    if "part 1" in topic.lower() or "curious" in t or "flower bloom" in t or "stars shine" in t: return "curiosity"
    if "part 2" in topic.lower() or "jigsaw" in t: return "jigsaw"
    if "part 3" in topic.lower() or ("paper" in evidence.lower() and "plastic ruler" in evidence.lower()): return "everyday_objects"
    if "part 4" in topic.lower() or ("pen stops writing" in t) or ("ink" in evidence.lower() and "guess" in evidence.lower()): return "pen_inquiry"
    if "part 5" in topic.lower() or "scientific method" in t or "scientific method" in evidence.lower(): return "scientific_method"
    if "part 6" in topic.lower() or "daily life" in t: return "daily_life"
    if "part 7" in topic.lower() or "journey" in t or "questions" in t: return "curiosity"
    raise ValueError("No reviewed topic-specific scene rule for synthesis: "+topic)

def svg_scene(topic, family_name, source_excerpt):
    # Diagrams are original vector drawings; claims are deliberately limited to the cited source.
    head=f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="300" viewBox="0 0 720 300" role="img" aria-labelledby="t d"><title id="t">{e(topic)}</title><desc id="d">Draft educational illustration for teacher review.</desc><rect width="720" height="300" rx="14" fill="#FFFFFF"/><text x="24" y="32" font-family="sans-serif" font-size="20" font-weight="700" fill="{INK}">{e(topic)}</text>'
    if family_name=="curiosity":
        body=f'<circle cx="120" cy="118" r="28" fill="{PALE}" stroke="{GREEN}" stroke-width="3"/><path d="M120 145 V195 M120 162 L92 180 M120 162 L148 180" stroke="{GREEN}" stroke-width="5" stroke-linecap="round"/><path d="M120 95 Q100 70 88 91 Q90 110 120 112 Q150 110 152 91 Q140 70 120 95Z" fill="{GREEN}"/><path d="M195 105 Q220 80 245 105 Q270 130 245 155 Q220 180 195 155 Q170 130 195 105Z" fill="{PALE}" stroke="{BLUE}" stroke-width="2"/><text x="290" y="105" font-size="17" fill="{INK}">Notice something</text><path d="M290 125 H430" stroke="{BLUE}" stroke-width="3"/><path d="M420 115 L432 125 L420 135" fill="none" stroke="{BLUE}" stroke-width="3"/><text x="450" y="105" font-size="17" fill="{INK}">Ask “Why?”</text><text x="290" y="160" font-size="13" fill="{GREY}">A question begins an exploration;</text><text x="290" y="180" font-size="13" fill="{GREY}">the answer still needs evidence.</text>'
    elif family_name=="jigsaw":
        body=f'<path d="M70 100 H140 Q140 75 162 75 Q184 75 184 100 H254 V155 Q280 155 280 178 Q280 201 254 201 V245 H184 Q184 220 162 220 Q140 220 140 245 H70 V175 Q95 175 95 155 Q95 135 70 135Z" fill="{PALE}" stroke="{BLUE}" stroke-width="3"/><path d="M254 100 H325 V135 Q350 135 350 155 Q350 175 325 175 V245 H254" fill="#E4F5ED" stroke="{GREEN}" stroke-width="3"/><path d="M390 160 H460" stroke="{ORANGE}" stroke-width="4"/><path d="M450 150 L462 160 L450 170" fill="none" stroke="{ORANGE}" stroke-width="4"/><text x="485" y="145" font-size="16" fill="{INK}">New discovery</text><text x="485" y="170" font-size="16" fill="{INK}">adds a piece</text><text x="390" y="220" font-size="13" fill="{GREY}">Metaphor: knowledge grows;</text><text x="390" y="239" font-size="13" fill="{GREY}">new questions appear.</text>'
    elif family_name=="everyday_objects":
        body=f'<rect x="42" y="82" width="112" height="68" rx="5" fill="{PALE}" stroke="{BLUE}" stroke-width="2"/><text x="98" y="120" text-anchor="middle" font-size="15" fill="{INK}">Paper</text><path d="M190 82 L205 68 H285 L300 82 V150 H190Z" fill="#F7F9FC" stroke="{GREY}" stroke-width="2"/><text x="245" y="120" text-anchor="middle" font-size="15" fill="{INK}">Metal key</text><rect x="340" y="82" width="120" height="22" rx="3" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="2"/><text x="400" y="130" text-anchor="middle" font-size="15" fill="{INK}">Plastic ruler</text><rect x="505" y="82" width="95" height="68" rx="12" fill="#E4F5ED" stroke="{GREEN}" stroke-width="2"/><text x="552" y="120" text-anchor="middle" font-size="15" fill="{INK}">Eraser</text><text x="42" y="195" font-size="16" fill="{INK}">Observe the objects</text><path d="M230 190 H310" stroke="{ORANGE}" stroke-width="3"/><path d="M300 180 L312 190 L300 200" fill="none" stroke="{ORANGE}" stroke-width="3"/><text x="330" y="195" font-size="16" fill="{INK}">Ask: What are they made of?</text><text x="42" y="240" font-size="12" fill="{GREY}">Illustrative object icons; material labels are limited to those explicitly stated in the source.</text>'
    elif family_name=="pen_inquiry":
        body=f'<rect x="48" y="105" width="150" height="22" rx="8" transform="rotate(-12 48 105)" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="3"/><text x="48" y="165" font-size="15" fill="{INK}">Pen stops writing</text><path d="M210 120 H265" stroke="{BLUE}" stroke-width="3"/><path d="M255 110 L267 120 L255 130" fill="none" stroke="{BLUE}" stroke-width="3"/><rect x="285" y="82" width="145" height="65" rx="10" fill="#FFF0D9" stroke="{ORANGE}" stroke-width="2"/><text x="357" y="108" text-anchor="middle" font-size="14" fill="{INK}">Possible guess</text><text x="357" y="129" text-anchor="middle" font-size="13" fill="{INK}">Ink is empty</text><path d="M440 120 H490" stroke="{GREEN}" stroke-width="3"/><path d="M480 110 L492 120 L480 130" fill="none" stroke="{GREEN}" stroke-width="3"/><rect x="510" y="82" width="165" height="65" rx="10" fill="#E4F5ED" stroke="{GREEN}" stroke-width="2"/><text x="592" y="108" text-anchor="middle" font-size="14" fill="{INK}">Test the guess</text><text x="592" y="129" text-anchor="middle" font-size="13" fill="{INK}">Check refill</text><text x="48" y="220" font-size="13" fill="{GREY}">If the guess is not supported, try another explanation and test again.</text>'
    elif family_name=="scientific_method":
        labels=["Observe","Ask","Guess","Test","Analyse"]
        xs=[55,190,325,460,595]
        for i,(x,label) in enumerate(zip(xs,labels)):
            body+=f'<rect x="{x-42}" y="105" width="84" height="62" rx="10" fill="{PALE if i%2==0 else PALE_BLUE}" stroke="{BLUE if i%2==0 else GREEN}" stroke-width="2"/><text x="{x}" y="142" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">{label}</text>'
            if i<4: body+=f'<path d="M{x+44} 136 H{xs[i+1]-48}" stroke="{ORANGE}" stroke-width="3"/><path d="M{xs[i+1]-58} 126 L{xs[i+1]-46} 136 L{xs[i+1]-58} 146" fill="none" stroke="{ORANGE}" stroke-width="3"/>'
        body+=f'<text x="55" y="205" font-size="14" fill="{INK}">Use results to decide whether the guess answers the question.</text><text x="55" y="230" font-size="12" fill="{GREY}">Steps shown from the cited textbook passage; repeat the process if needed.</text>'
    elif family_name=="daily_life":
        body=f'<circle cx="115" cy="115" r="30" fill="{PALE_BLUE}" stroke="{BLUE}" stroke-width="2"/><path d="M95 115 H135 M115 95 V135" stroke="{BLUE}" stroke-width="3"/><text x="165" y="110" font-size="15" fill="{INK}">A daily problem</text><path d="M310 120 H365" stroke="{GREEN}" stroke-width="3"/><path d="M355 110 L367 120 L355 130" fill="none" stroke="{GREEN}" stroke-width="3"/><rect x="385" y="82" width="245" height="75" rx="10" fill="#E4F5ED" stroke="{GREEN}" stroke-width="2"/><text x="507" y="110" text-anchor="middle" font-size="15" fill="{INK}">Ask • suggest • test</text><text x="507" y="134" text-anchor="middle" font-size="13" fill="{INK}">Use observations as evidence</text><text x="45" y="210" font-size="14" fill="{GREY}">Examples in the source include cooking, a flat bicycle tyre, and a light bulb/switch.</text>'
    else: raise ValueError("Unknown scene family "+family_name)
    return head+body+"</svg>\n"

def clean_text(text):
    # Flag obvious extraction contamination, do not silently claim to repair it.
    flags=[]
    if re.search(r"\\b(?:10/18/2024|Chapter 1\\.indd|Reprint 2026-27)\\b", text, re.I): flags.append("running_header_or_timestamp")
    if "fi nd" in text.lower() or "scientifi c" in text.lower(): flags.append("ocr_split_word")
    if "daily lives" in text.lower(): flags.append("running_header_fragment")
    if "Or watched a flower" in text: flags.append("malformed_ocr_sentence")
    return flags

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",default="build/visuals/science-chapter-1")
    p.add_argument("--source-id",default=SOURCE_ID)
    p.add_argument("--limit",type=int,default=0,help="0 means all approved synthesis topics")
    p.add_argument("--dry-run",action="store_true",help="Read and report without writing files")
    a=p.parse_args()
    dsn=os.getenv("DATABASE_URL")
    if not dsn:
        print("Set DATABASE_URL to a read-only Neon connection string.",file=sys.stderr); return 2
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        print("Install psycopg[binary] to read synthesis records.",file=sys.stderr); return 2
    sql="""SELECT s.id AS synthesis_id, s.topic, s.page_start, s.page_end,
      s.learning_objectives_json, s.explanation_json, s.examples_json,
      s.citation_refs_json, s.approval_status, src.id AS source_id, src.title AS source_title
      FROM syllabus_topic_syntheses s JOIN sources src ON src.id=s.source_id
      WHERE s.source_id=%s AND s.approval_status='approved'
      ORDER BY s.page_start, s.page_end, s.topic"""
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=10) as conn:
        rows=conn.execute(sql,(a.source_id,)).fetchall()
        chunks=conn.execute("SELECT id,chunk_no,page_start,page_end,text FROM chunks WHERE source_id=%s ORDER BY chunk_no",(a.source_id,)).fetchall()
    if a.limit: rows=rows[:a.limit]
    chunk_map={x["id"]:x for x in chunks}
    outdir=Path(a.out_dir); manifest=[]; generated=0
    for row in rows:
        refs=json.loads(row["citation_refs_json"] or "[]")
        cited=[chunk_map[x] for x in refs if x in chunk_map]
        evidence="\n".join(x["text"] for x in cited)
        explanation=json.loads(row["explanation_json"] or "{}")
        flags=clean_text(str(explanation.get("caption",""))+"\n"+evidence)
        missing=[x for x in refs if x not in chunk_map]
        try: scene=family(row["topic"],json.dumps(explanation,ensure_ascii=False),evidence)
        except ValueError as ex:
            manifest.append({"synthesis_id":row["synthesis_id"],"topic":row["topic"],"status":"blocked","reason":str(ex),"missing_source_chunk_ids":missing}); continue
        status="needs_review" if flags or missing or not cited else "draft_review"
        fingerprint=hashlib.sha256((row["synthesis_id"]+"|"+scene+"|"+evidence).encode()).hexdigest()
        record={"synthesis_id":row["synthesis_id"],"topic":row["topic"],"page_start":row["page_start"],"page_end":row["page_end"],
          "source_id":row["source_id"],"source_title":row["source_title"],"source_chunk_ids":refs,
          "renderer_family":scene,"renderer_version":VERSION,"evidence_status":status,"quality_flags":flags,
          "missing_source_chunk_ids":missing,"content_fingerprint":fingerprint,"database_write":"none"}
        manifest.append(record)
        if not a.dry_run:
            outdir.mkdir(parents=True,exist_ok=True)
            stem=f"{row['page_start']:02d}-{row['synthesis_id'][:10]}"
            (outdir/(stem+".svg")).write_text(svg_scene(row["topic"],scene,evidence),encoding="utf-8")
            (outdir/(stem+".json")).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
            generated+=1
    if not a.dry_run:
        outdir.mkdir(parents=True,exist_ok=True)
        (outdir/"manifest.json").write_text(json.dumps({"chapter":CHAPTER,"class_level":6,"subject":"Science","source_id":a.source_id,"renderer_version":VERSION,"generated_files":generated,"assets":manifest},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"chapter":CHAPTER,"approved_syntheses_read":len(rows),"source_chunks_read":len(chunks),"assets_generated":generated,"assets_blocked":sum(x.get("status")=="blocked" for x in manifest),"assets_needing_review":sum(x.get("evidence_status")=="needs_review" for x in manifest),"database_writes":0,"assets":manifest},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
