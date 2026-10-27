from scripts.apply_class6_math_qa_corrections import revise_lesson
from syllabus_synthesis import validate_chapter_lesson_payload


CHUNK = "qa-chunk"


def _step(title, teacher, visual_text=""):
    return {
        "id": title.lower().replace(" ", "-"),
        "title": title,
        "teacher_says": teacher,
        "caption": "A clear lesson caption.",
        "example": "A source-supported example.",
        "misconception": "Avoid confusing the concepts.",
        "checkpoint": "What did we learn?",
        "learning_objectives": ["Explain the idea."],
        "source_chunk_ids": [CHUNK],
        "visual": {
            "type": "diagram" if visual_text else "none",
            "objects": [],
            "actions": [],
            "narration_sync": [visual_text] if visual_text else [],
        },
    }


def _lesson(chapter, steps):
    return {
        "chapter_title": chapter,
        "overview": "A source-grounded overview.",
        "learning_objectives": ["Explain the key idea."],
        "concept_map": [{
            "concept": "Key idea",
            "prerequisite": "",
            "source_chunk_ids": [CHUNK],
        }],
        "teaching_sequence": steps,
    }


def test_fractions_qa_corrections_pass_content_validation():
    lesson = _lesson("Fractions", [
        _step(
            "Parts of a Whole and Reading Fractions",
            "A whole chikki divided into 6 equal parts gives six 1/6 pieces.",
            "A whole chikki broken into 3 equal pieces yields pieces of 1/3 chikki each.",
        ),
        _step(
            "Marking Fractions on the Number Line",
            "Divide the interval into 2 equal parts and 3 equal parts.",
            "The distance from 0 to 1 is divided into 5 equal parts.",
        ),
        _step(
            "History of Fractions and Unit Fraction Puzzles",
            "The Rig Veda uses tri-pada. Ancient texts used notation very similar to ours.",
        ),
    ])
    revised, changes = revise_lesson("Fractions", lesson)
    result = validate_chapter_lesson_payload(revised, {CHUNK})
    assert result["valid"], result["errors"]
    assert len(changes) == 3


def test_data_handling_qa_corrections_pass_content_validation():
    lesson = _lesson("Data Handling and Presentation", [
        _step(
            "Organising Data and Tally Marks",
            "He crossed every fifth mark as |||| to count preferences.",
        ),
        _step("Warm-up: What is Data?", "A collection of information is data."),
    ])
    revised, changes = revise_lesson("Data Handling and Presentation", lesson)
    result = validate_chapter_lesson_payload(revised, {CHUNK})
    assert result["valid"], result["errors"]
    assert revised["teaching_sequence"][1]["visual"]["type"] == "table"
    assert len(changes) == 2


def test_perimeter_and_area_qa_corrections_pass_content_validation():
    lesson = _lesson("Perimeter and Area", [
        _step(
            "Tracks, Estimations, and Straight vs. Diagonal Units",
            "A diagonal line is longer than a straight grid unit!",
        ),
        _step(
            "Area of Triangles and Composite Shapes",
            "Any rectangle cut along its diagonal gives two triangles of equal area. "
            "Therefore, the area of a triangle is always half the area of the corresponding rectangle "
            "(or half of base times height).",
        ),
    ])
    revised, changes = revise_lesson("Perimeter and Area", lesson)
    result = validate_chapter_lesson_payload(revised, {CHUNK})
    assert result["valid"], result["errors"]
    assert len(changes) == 2
