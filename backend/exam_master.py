"""Exam Master MVP: curated Class 6 NCERT Science practice questions and two printable PDFs."""
from __future__ import annotations

import base64
import io
import random
import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

router = APIRouter(prefix="/exam-master", tags=["Exam Master"])
CHAPTERS = [
    "The Wonderful World of Science", "Diversity in the Living World",
    "Mindful Eating: A Path to a Healthy Body", "Exploring Magnets",
    "Measurement of Length and Motion", "Materials Around Us",
    "Temperature and its Measurement", "A Journey through States of Water",
    "Methods of Separation in Everyday Life", "Living Creatures: Exploring their Characteristics",
    "Nature's Treasures", "Beyond Earth",
]
# These are original syllabus-aligned practice questions, not verbatim textbook questions.
BANK: dict[str, list[dict[str, Any]]] = {
"The Wonderful World of Science": [
("What is science? Give one example of a question that science can help us answer.",2,"exercise_variant","Science is a way of learning about the natural world through observations, questions and investigations. Example: Why do shadows change length?"),
("Write two steps you would follow to investigate which paper absorbs more water.",2,"exercise_variant","Ask a testable question; use equal-sized paper pieces and equal amounts of water; keep conditions the same; observe and record results. Any two sensible steps."),
("Why should we change only one factor at a time in a fair test?",2,"exercise_variant","So that any difference in the result can be linked to the factor being tested."),
("A plant near a window grows towards the light. State one observation and one question you could investigate.",2,"exercise_variant","Observation: the plant bends/grows towards the window. Question: does the direction or amount of light affect its growth?"),
("A student observes that wet clothes dry faster on a sunny, windy day. Identify two conditions that may affect drying.",2,"inside_chapter","Sunlight/temperature and wind/air movement can affect the rate of drying."),
],
"Diversity in the Living World": [
("What is biodiversity? Give one example.",2,"exercise_variant","Biodiversity is the variety of living organisms in an area. Example: different plants, birds and insects in a garden."),
("Write two differences between herbs and trees.",2,"exercise_variant","Herbs are usually small with soft green stems; trees are generally tall and have a hard woody trunk."),
("Why are leaves useful when comparing different plants?",2,"exercise_variant","Leaf shape, size, arrangement and venation can help us observe similarities and differences among plants."),
("Group a fish, a sparrow and a butterfly by one feature they share and one feature that differs.",3,"exercise_variant","All are animals. Fish live in water and use gills; sparrows have feathers and wings; butterflies are insects with six legs and wings."),
("A school garden has grass, ants, butterflies and a neem tree. Give two examples of diversity found there.",2,"inside_chapter","Different kinds of plants and animals; different sizes, body structures, habitats or ways of moving."),
],
"Mindful Eating: A Path to a Healthy Body": [
("Name the main nutrients in food and state one function of any two.",3,"exercise_variant","Carbohydrates, proteins, fats, vitamins, minerals; water and dietary fibre are also important. Carbohydrates provide energy; proteins support growth and repair; other correct functions accepted."),
("Why is a balanced diet important for a growing child?",2,"exercise_variant","It supplies different nutrients and energy needed for growth, repair and good health."),
("Give two examples of foods that are rich in protein.",2,"exercise_variant","Examples: pulses, beans, milk, eggs, fish, meat, soybeans or nuts."),
("What is the role of dietary fibre and water in our diet?",2,"exercise_variant","Fibre helps bowel movement/digestion; water supports body functions and helps prevent dehydration."),
("A lunch contains rice, dal, vegetables and curd. Explain why eating different food groups is useful.",2,"inside_chapter","Different foods supply different nutrients; together they help make the meal more balanced."),
],
"Exploring Magnets": [
("Name two materials that are attracted by a magnet and two that are not usually attracted.",2,"exercise_variant","Attracted: iron/steel, nickel or cobalt. Not usually attracted: wood, plastic, paper, copper or aluminium."),
("What are the two poles of a bar magnet? Describe what happens when like poles are brought together.",2,"exercise_variant","North and south poles; like poles repel."),
("How can you use a freely suspended bar magnet to find directions?",2,"exercise_variant","When it settles, it aligns approximately north–south; identify the north-seeking end."),
("Why should a magnet be stored carefully and kept away from some electronic devices?",2,"exercise_variant","Rough handling/heating can weaken some magnets; magnets can interfere with magnetic storage or sensitive devices."),
("A student brings the north pole of one magnet near the north pole of another. Predict what happens and name the force.",2,"inside_chapter","They repel each other; this is magnetic repulsion."),
],
"Measurement of Length and Motion": [
("Why should we use a standard unit to measure length?",2,"exercise_variant","Standard units make measurements consistent and comparable between people and places."),
("Convert 2 metres into centimetres.",1,"exercise_variant","2 m = 200 cm."),
("How should you place a ruler to measure the length of a pencil accurately?",2,"exercise_variant","Align the zero mark with one end, keep the ruler straight along the pencil and read the other end at eye level. If zero is damaged, subtract the start reading."),
("Distinguish between rectilinear and circular motion with one example each.",2,"exercise_variant","Rectilinear motion is along a straight line (e.g. lift moving vertically); circular motion follows a circular path (e.g. a fan blade)."),
("A toy car travels a longer distance in the same time than yesterday. What can you infer about its motion?",2,"inside_chapter","Its average speed was greater, assuming the time interval is the same."),
],
"Materials Around Us": [
("What is a material? Give two examples of objects made from different materials.",2,"exercise_variant","A material is the substance from which an object is made; e.g. glass tumbler, wooden chair."),
("Name two properties that can be used to group materials.",2,"exercise_variant","Hardness, appearance/lustre, solubility, transparency, magnetism, flexibility or ability to float/sink."),
("What is the difference between transparent and opaque materials?",2,"exercise_variant","Transparent materials let most light pass so objects can be seen clearly; opaque materials do not let light pass through."),
("Why is glass used for windows while wood is often used for doors?",2,"exercise_variant","Glass is transparent and lets light in; wood is opaque and gives privacy/strength."),
("A material floats on water. Does this alone prove it is soluble in water? Explain.",2,"inside_chapter","No. Floating describes whether it stays at the surface; solubility describes whether it dissolves. They are different properties."),
],
"Temperature and its Measurement": [
("What does a thermometer measure? Write the common unit used in school science.",2,"exercise_variant","Temperature; degree Celsius (°C)."),
("Why should a clinical thermometer be read according to its instructions and not used for hot objects?",2,"exercise_variant","It is designed for body-temperature ranges and safe use; hot objects can exceed its range or damage it."),
("State one safety precaution while using a laboratory thermometer.",1,"exercise_variant","Handle carefully, keep it upright as appropriate, do not use it to stir, and read at eye level without touching the bulb."),
("Why is touching an object not a reliable way to compare its temperature?",2,"exercise_variant","Our skin adapts and can give misleading sensations; a thermometer gives a more objective measurement."),
("A thermometer shows 30°C in one room and 24°C in another. Which room is warmer and by how many degrees?",2,"inside_chapter","The first room is warmer by 6°C."),
],
"A Journey through States of Water": [
("Name the three common states of water.",1,"exercise_variant","Solid (ice), liquid water and water vapour/gas."),
("What is evaporation? Give one everyday example.",2,"exercise_variant","Change of liquid into vapour from its surface; e.g. drying clothes or a puddle disappearing."),
("Explain condensation with one example.",2,"exercise_variant","Water vapour cools and changes to liquid; e.g. droplets on the outside of a cold glass."),
("How does heating affect ice and liquid water?",2,"exercise_variant","Ice melts into liquid water; with further heating water can boil and change into water vapour."),
("Water droplets appear on the outside of a chilled bottle. Where did the water come from?",2,"inside_chapter","Water vapour in the surrounding air cooled on the bottle and condensed into liquid droplets."),
],
"Methods of Separation in Everyday Life": [
("Which method can be used to separate stones from rice? Explain.",2,"exercise_variant","Handpicking, because the larger visible stones can be picked out by hand."),
("How can sand be separated from water?",2,"exercise_variant","Filtration or sedimentation followed by decantation."),
("What is sieving? Give one use.",2,"exercise_variant","Passing a mixture through a mesh to separate particles by size; e.g. separating bran/lumps from flour."),
("Which method would you use to obtain salt from salt water? State the principle.",2,"exercise_variant","Evaporation; water evaporates and salt remains."),
("A mixture contains iron filings and sand. Suggest a suitable method and explain why it works.",2,"inside_chapter","Use a magnet to attract the iron filings while the sand is not attracted."),
],
"Living Creatures: Exploring their Characteristics": [
("Write any three characteristics of living organisms.",3,"exercise_variant","Any three: need food/energy, grow, respire, respond to stimuli, reproduce, excrete, have a life cycle."),
("How is growth in a plant different from an increase in the size of a non-living object?",2,"exercise_variant","A plant grows through living processes and uses nutrients; a non-living object may become bigger only by addition of material."),
("Why do living organisms need food?",2,"exercise_variant","For energy, growth, repair and maintenance of life processes."),
("Give one example of a response to a stimulus in a plant and one in an animal.",2,"exercise_variant","Plant bends towards light/touch-me-not leaves fold; animal withdraws from heat or moves towards food."),
("A seed is not moving. Give one reason why it is still considered living.",2,"inside_chapter","It can germinate and grow under suitable conditions; lack of visible movement does not mean it is non-living."),
],
"Nature's Treasures": [
("Name two natural resources and state one use of each.",2,"exercise_variant","Examples: water for drinking/irrigation; soil for growing plants; air for respiration; forests for habitats/materials."),
("Why should we avoid wasting fresh water?",2,"exercise_variant","Usable fresh water is limited and needed by people, plants and animals; conserving it protects supplies."),
("Give two ways forests support living organisms.",2,"exercise_variant","Provide habitats, food, oxygen, help protect soil/water cycle and support biodiversity."),
("What is the difference between renewable and non-renewable resources? Give one example of each.",3,"exercise_variant","Renewable resources are replenished naturally on a human timescale (sunlight); non-renewable resources are finite/formed very slowly (coal/petroleum)."),
("A school turns off taps and plants native trees. Explain how these actions help protect nature.",2,"inside_chapter","They conserve water and support local biodiversity/provide habitat and protect soil."),
],
"Beyond Earth": [
("What is a constellation? Name one familiar constellation.",2,"exercise_variant","A recognised pattern of stars; e.g. Ursa Major/Saptarishi or Orion."),
("How is a star different from a planet in the way it produces light?",2,"exercise_variant","A star emits its own light; a planet is seen mainly by reflecting light from a star."),
("Why does the Moon appear bright at night?",2,"exercise_variant","It reflects sunlight; it does not produce its own visible light like a star."),
("What is the solar system? Name its central star.",2,"exercise_variant","The Sun and the objects bound to it, including planets and other smaller bodies; the Sun is the central star."),
("Why do stars appear to change position across the night sky?",2,"inside_chapter","Because Earth rotates, making stars appear to move across the sky."),
],
}

class ExamMasterRequest(BaseModel):
    board: str = Field(default="CBSE", min_length=2, max_length=80)
    class_level: int = Field(default=6, ge=6, le=6)
    subject: str = Field(default="Science", min_length=1, max_length=80)
    medium: str = Field(default="English", min_length=2, max_length=40)
    selected_chapters: list[str] = Field(default_factory=lambda: CHAPTERS[:3], min_length=1, max_length=12)
    question_count: int = Field(default=15, ge=5, le=60)
    student_name: str = Field(default="", max_length=100)
    school_name: str = Field(default="", max_length=120)
    exam_title: str = Field(default="Practice Examination", max_length=120)
    seed: int | None = None

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ExamTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=TA_CENTER, textColor=colors.black, spaceAfter=5))
    styles.add(ParagraphStyle(name="ExamSub", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14, alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="QText", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, spaceAfter=3))
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11))
    return styles

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0]/2, 10*mm, f"PadippuPal Exam Master  •  Page {doc.page}")
    canvas.restoreState()

def _pdf(story):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=18*mm, title="PadippuPal Exam Master")
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()

def _safe(text: str) -> str:
    from xml.sax.saxutils import escape
    return escape(str(text)).replace("\n", "<br/>")

def _select_questions(req: ExamMasterRequest):
    rng = random.Random(req.seed)
    selected = []
    for chapter in req.selected_chapters:
        if chapter not in BANK:
            raise HTTPException(status_code=422, detail=f"Unsupported or unavailable chapter: {chapter}")
        for q, marks, category, answer in BANK[chapter]:
            selected.append({"chapter": chapter, "question": q, "marks": marks, "category": category, "answer": answer})
    rng.shuffle(selected)
    target = min(req.question_count, len(selected))
    # Aim for 80:20 by question count, while retaining a transparent provenance label.
    book = [q for q in selected if q["category"] == "exercise_variant"]
    inside = [q for q in selected if q["category"] == "inside_chapter"]
    book_target = round(target * 0.8)
    inside_target = target - book_target
    chosen = book[:book_target] + inside[:inside_target]
    if len(chosen) < target:
        remaining = [q for q in selected if q not in chosen]
        chosen.extend(remaining[:target-len(chosen)])
    rng.shuffle(chosen)
    return chosen

def _paper_pdf(req, questions, total):
    st = _styles()
    story = [Paragraph(_safe(req.school_name or "PadippuPal"), st["ExamTitle"]),
             Paragraph(_safe(req.exam_title), st["ExamTitle"]),
             Paragraph(f"Class {req.class_level} · {_safe(req.subject)} · {_safe(req.board)}", st["ExamSub"]),
             Paragraph(f"Chapters: {_safe('; '.join(dict.fromkeys(q['chapter'] for q in questions)))}", st["ExamSub"]),
             Spacer(1, 5*mm)]
    student = req.student_name.strip() or "________________________________"
    story += [Paragraph(f"Name: {_safe(student)} &nbsp;&nbsp;&nbsp; Date: __________________", st["Normal"]),
              Paragraph(f"Time: ____________ &nbsp;&nbsp;&nbsp; Maximum marks: {total}", st["Normal"]), Spacer(1, 4*mm),
              Paragraph("<b>Instructions</b>", st["Heading3"]),
              Paragraph("1. Read each question carefully.  2. Answer all questions.  3. Marks are shown in brackets. 4. Write neatly and show your working where needed.", st["QText"]),
              Spacer(1, 3*mm)]
    current_chapter = None
    for i, q in enumerate(questions, 1):
        if q["chapter"] != current_chapter:
            current_chapter = q["chapter"]
            story.append(Paragraph(_safe(current_chapter), st["Heading3"]))
        story.append(KeepTogether([Paragraph(f"<b>{i}.</b> {_safe(q['question'])} <b>[{q['marks']} marks]</b>", st["QText"]),
                                   Spacer(1, max(3, q["marks"] * 3)*mm)]))
    story += [Spacer(1, 5*mm), Paragraph("<b>Score sheet</b>", st["Heading3"]),
              Paragraph(f"Marks obtained: ______ / {total} &nbsp;&nbsp; Percentage: ______% &nbsp;&nbsp; Parent signature: __________________", st["QText"])]
    return _pdf(story)

def _key_pdf(req, questions, total, book_count, inside_count):
    st = _styles()
    story = [Paragraph("PARENT ANSWER KEY", st["ExamTitle"]),
             Paragraph(f"Class {req.class_level} · {_safe(req.subject)} · {_safe(req.board)}", st["ExamSub"]),
             Paragraph(f"Total: {total} marks · Questions: {len(questions)}", st["ExamSub"]),
             Paragraph(f"Question-source mix: {book_count} exercise-based practice variants, {inside_count} inside-chapter questions. These are original practice questions, not verbatim book-back questions or predictions.", st["SmallNote"]), Spacer(1, 4*mm)]
    for i, q in enumerate(questions, 1):
        story.append(KeepTogether([
            Paragraph(f"<b>{i}. {_safe(q['question'])}</b> <b>[{q['marks']} marks]</b>", st["QText"]),
            Paragraph(f"<b>Chapter:</b> {_safe(q['chapter'])}", st["SmallNote"]),
            Paragraph(f"<b>Model answer:</b> {_safe(q['answer'])}", st["QText"]),
            Paragraph(f"<b>Suggested mark-wise rubric ({q['marks']} marks):</b> " + (("1 mark for the correct fact, term or result." if q["marks"] == 1 else "Award up to 1 mark for each distinct correct point or a correct point plus a suitable explanation/example; maximum 2 marks." if q["marks"] == 2 else "Award up to 1 mark for each distinct correct point, explanation or valid example; maximum 3 marks." if q["marks"] == 3 else "Award credit for each correct required step; maximum " + str(q["marks"]) + " marks.")) + " Accept scientifically equivalent wording and appropriate examples. Do not require memorised wording.", st["SmallNote"]),
            Spacer(1, 3*mm)]))
    story += [PageBreak(), Paragraph("PARENT SCORE SHEET", st["ExamTitle"]),
              Paragraph(f"Student: {_safe(req.student_name or '____________________________')} &nbsp;&nbsp; Date: ______________", st["Normal"]),
              Spacer(1, 4*mm)]
    data = [["Q.No.", "Marks", "Awarded"], *[[str(i), str(q["marks"]), "______"] for i,q in enumerate(questions,1)], ["TOTAL", str(total), "______"]]
    table = Table(data, colWidths=[30*mm, 30*mm, 40*mm], repeatRows=1)
    table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.black),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),9),("PADDING",(0,0),(-1,-1),5),("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story += [table, Spacer(1, 5*mm), Paragraph("Parent marking notes", st["Heading2"]),
              Paragraph("• Give credit for correct scientific ideas even if the wording differs. • For multi-mark questions, award partial credit for each correct point. • Do not deduct for spelling or grammar unless language is being assessed. • Discuss mistakes kindly and revisit the chapter together.", st["QText"]),
              Paragraph("This is a practice paper in a school-exam style, not an official school paper. Formats vary between schools.", st["SmallNote"])]
    return _pdf(story)

@router.get("/catalog")
def exam_master_catalog():
    return {"board":"CBSE","class_level":6,"subject":"Science","mediums":["English"],"chapters":[{"chapter_number":i+1,"title":title,"question_count":len(BANK[title])} for i,title in enumerate(CHAPTERS)],"question_bank_count":sum(map(len,BANK.values())),"question_policy":"Original syllabus-aligned practice variants; not verbatim textbook exercise questions.","pdfs":["student_question_paper","parent_answer_key"]}

@router.post("/generate")
def generate_exam_master(req: ExamMasterRequest):
    if req.board.strip().casefold() != "cbse" or req.class_level != 6 or req.subject.strip().casefold() != "science":
        raise HTTPException(status_code=422, detail="Exam Master currently supports CBSE/NCERT Class 6 Science only.")
    if any(c not in CHAPTERS for c in req.selected_chapters):
        raise HTTPException(status_code=422, detail="Select chapters from the supplied Class 6 NCERT Science catalogue.")
    questions = _select_questions(req)
    if not questions:
        raise HTTPException(status_code=422, detail="No questions available for the selected chapters.")
    total = sum(q["marks"] for q in questions)
    book_count = sum(q["category"] == "exercise_variant" for q in questions)
    inside_count = sum(q["category"] == "inside_chapter" for q in questions)
    student_pdf = _paper_pdf(req, questions, total)
    key_pdf = _key_pdf(req, questions, total, book_count, inside_count)
    return {"paper_id":str(uuid.uuid4()),"status":"generated","board":req.board,"class_level":req.class_level,"subject":req.subject,"selected_chapters":list(dict.fromkeys(q["chapter"] for q in questions)),"question_count":len(questions),"maximum_marks":total,"source_mix":{"exercise_based_practice_variants":book_count,"inside_chapter":inside_count,"note":"Exercise-based variants are original practice questions, not verified verbatim book-back questions."},"student_pdf_base64":base64.b64encode(student_pdf).decode("ascii"),"parent_key_pdf_base64":base64.b64encode(key_pdf).decode("ascii"),"filenames":{"student":"PadippuPal_Student_Question_Paper.pdf","parent_key":"PadippuPal_Parent_Answer_Key.pdf"}}
