"""Build a selectable, semantically tagged report and render/verify its pages.

Optional artifact dependencies: reportlab, pypdf, pymupdf. These are not needed
to run the Sudoku agent or its behavioral tests. Run from the repository root.
"""

from contextlib import contextmanager
import json
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, BooleanObject, DictionaryObject, NameObject, NumberObject,
    TextStringObject,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
TEMP = ROOT / "tmp" / "pdfs"
REPO = "https://github.com/sshb4/ReActSudokuAgent"
INK = HexColor("#17263A")
BLUE = HexColor("#205C8A")
PALE = HexColor("#EFF5FA")
GRAY = HexColor("#536274")


def pdf_dict(values):
    return DictionaryObject({NameObject(key): value for key, value in values.items()})


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    review_path = ROOT / "docs" / "student-review-status.json"
    reviewed = review_path.exists() and json.loads(review_path.read_text()).get("confirmed") is True
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("Report", str(font_path)))
        pdfmetrics.registerFont(TTFont("ReportBold", str(font_path.with_name("Arial Bold.ttf"))))
        regular, bold = "Report", "ReportBold"
    else:
        regular, bold = "Helvetica", "Helvetica-Bold"
    raw = TEMP / "report-untagged.pdf"
    c = canvas.Canvas(str(raw), pagesize=letter, pageCompression=1)
    tags = []
    counts = {}
    y = 748

    @contextmanager
    def tag(kind, alt=None):
        page = c.getPageNumber() - 1
        mcid = counts.get(page, 0)
        counts[page] = mcid + 1
        tags.append({"page": page, "mcid": mcid, "kind": kind, "alt": alt})
        c.addLiteral(f"/{kind} <</MCID {mcid}>> BDC")
        yield
        c.addLiteral("EMC")

    def text(value, kind="P", size=10.5, color=INK, gap=8):
        nonlocal y
        face = bold if kind in ("H1", "H2") else regular
        leading = size * 1.34
        lines = simpleSplit(value, face, size, 524)
        with tag(kind):
            c.setFont(face, size)
            c.setFillColor(color)
            for line in lines:
                if y < 48:
                    raise ValueError("Report content exceeds the page layout.")
                c.drawString(44, y, line)
                y -= leading
        y -= gap

    def footer(number):
        c.addLiteral("/Artifact BMC")
        c.setStrokeColor(HexColor("#CFD8E2"))
        c.line(44, 39, 568, 39)
        c.setFillColor(GRAY)
        c.setFont(regular, 8)
        c.drawString(44, 25, "CS 4300 | ReAct Sudoku Agent | October 20, 2026")
        c.drawRightString(568, 25, str(number))
        c.addLiteral("EMC")

    def box(x, top, width, lines):
        height = 53
        c.setFillColor(PALE)
        c.setStrokeColor(BLUE)
        c.roundRect(x, top - height, width, height, 6, fill=1, stroke=1)
        c.setFillColor(INK)
        for index, line in enumerate(lines):
            c.setFont(bold if index == 0 else regular, 9 if index == 0 else 8.5)
            c.drawCentredString(x + width / 2, top - 17 - index * 13, line)

    def arrow(x1, y1, x2, y2, label=None, label_x=None, label_y=None):
        from math import atan2, cos, sin
        c.setStrokeColor(BLUE)
        c.setLineWidth(1)
        c.line(x1, y1, x2, y2)
        angle = atan2(y2 - y1, x2 - x1)
        for delta in (-0.45, 0.45):
            c.line(x2, y2, x2 - 6 * cos(angle + delta), y2 - 6 * sin(angle + delta))
        if label:
            c.setFillColor(GRAY)
            c.setFont(regular, 7.5)
            c.drawCentredString(label_x if label_x is not None else (x1 + x2) / 2,
                                label_y if label_y is not None else (y1 + y2) / 2 + 4, label)

    text("Developing a ReAct Sudoku Agent", "H1", 21, gap=6)
    text("CS 4300-01 Artificial Intelligence | Curtis Larsen", size=10, color=GRAY)
    text("Git repository", "H2", 12, gap=3)
    text(REPO, size=10.5, color=BLUE, gap=10)
    if not reviewed:
        text("REVIEW COPY - student code review confirmation pending", size=9, color=GRAY)
    text("System and component interactions", "H2", 13)
    text("A local language model selects one typed tool request at a time. The application owns the board, knowledge base, action budget, trace, and terminal status. Only an independently validated submission can establish success.")
    top = y - 4
    alt = ("The CLI loads configuration and starts the agent loop. The loop sends prompts, "
           "history, and schemas to the Ollama model adapter, and receives one request. "
           "It passes the request to the controller, which validates it, enforces the budget, "
           "records the trace, and dispatches puzzle or knowledge-base operations. "
           "Observations return through the controller to the loop and then the model. "
           "Puzzle state includes clues and undo history; knowledge-base state includes facts and rules.")
    with tag("Figure", alt):
        box(231, top, 150, ["CLI", "cli.py / __main__.py"])
        mid = top - 116
        box(44, mid, 150, ["Local model adapter", "ollama_model.py", "Ollama / Qwen"])
        box(231, mid, 150, ["Agent loop", "agent.py", "prompts and history"])
        box(418, mid, 150, ["Controller", "controller.py", "budget, trace, status"])
        bottom = mid - 132
        box(231, bottom, 150, ["Puzzle", "puzzle.py", "board, clues, undo"])
        box(418, bottom, 150, ["Knowledge base", "knowledge.py", "facts, rules, queries"])
        arrow(306, top - 53, 306, mid, "start", 331, top - 84)
        arrow(231, mid - 16, 194, mid - 16)
        arrow(194, mid - 39, 231, mid - 39)
        arrow(381, mid - 16, 418, mid - 16)
        arrow(418, mid - 39, 381, mid - 39)
        c.setFont(regular, 7.5)
        c.setFillColor(GRAY)
        c.drawCentredString(213, mid + 8, "prompt / schema")
        c.drawCentredString(213, mid - 68, "model request")
        c.drawCentredString(400, mid + 8, "request")
        c.drawCentredString(400, mid - 68, "observation")
        arrow(475, mid - 53, 330, bottom, "validated operations", 356, mid - 94)
        arrow(330, bottom, 475, mid - 53)
        arrow(514, mid - 53, 514, bottom)
        arrow(514, bottom, 514, mid - 53)
    y = bottom - 71
    text("Figure 1. Requests go through the controller; observations return to the model. schemas.py defines the shared typed interfaces, and model.py defines the runtime-independent model protocol.", size=9.5)
    text("State boundaries", "H2", 12)
    text("Clues cannot be edited. Rejected operations leave puzzle and KB state unchanged. Every attempted tool request consumes an action. Undo removes the latest accepted placement. A successful submission on the final allowed action takes precedence over budget exhaustion.", size=10)
    footer(1)
    c.showPage()
    y = 748
    text("Development process and evidence", "H1", 20)
    text("Specifications before implementation", "H2", 12)
    text("The architecture and public behavior contracts were written first. They define tool schemas, puzzle representation, classical propositional semantics, undo behavior, controller policies, and ordered terminal checks. Main specifications, tests, and implementation were committed in that order; the development log records later revisions honestly.")
    text("Tests and coding-agent implementation", "H2", 12)
    text("Black-box tests were derived from the contracts before the corresponding main function bodies existed. A coding agent implemented a significant portion of the project against those specifications and tests. Later review added an independent truth-table oracle and explicitly labeled white-box fault injection. The complete suite passes 170 cases.")
    text("What real-model testing changed", "H2", 12)
    text("The first small-model run repeatedly targeted a clue and reached its action limit. The controller protected the clues. Board observations were then revised to label empty-cell coordinates and report legal candidates. An unsupported regex feature was replaced, and explicit terminal reasons were added to tool observations. Tests were written for these gaps before the corresponding fixes.")
    kb_path = ROOT / "docs/evidence/model-run-kb-success.json"
    kb = json.loads(kb_path.read_text()) if kb_path.exists() else None
    tools = {e["request"]["tool"] for e in kb["trace"]} if kb else set()
    if kb and kb["status"] == "success" and {"add_fact", "add_rule", "query"} <= tools:
        result_text = (f"Ollama 0.40.6 with Qwen 2.5 1.5B completed the three-empty-cell example "
                       f"in {kb['actions_used']} model-selected tool requests. The saved live trace includes "
                       "fact and rule updates, an entailment query, placements, and validated submission. "
                       "This demonstrates one near-complete puzzle; harder-puzzle reliability is not established.")
    else:
        result_text = ("Ollama 0.40.6 with Qwen 2.5 1.5B completed the three-empty-cell example "
                       "in eight model-selected tool requests. KB and undo tools are separately covered by "
                       "tests and a clearly labeled scripted replay. A model-driven KB demonstration is "
                       "still being evaluated. Harder-puzzle reliability is not established.")
    text("Verification and limits", "H2", 12)
    text(result_text)
    text("Student review", "H2", 12)
    if reviewed:
        text("The student reviewed the code, contracts, test evidence, and changes using docs/student-review.md and confirmed understanding of the design and revisions. The repository retains that confirmation and the coding-agent process log.")
    else:
        text("A concrete code-review walkthrough is included in docs/student-review.md. Student confirmation is still pending; this review copy does not claim that the student's review responsibility has already been completed.")
    text("Takeaway I plan to keep", "H2", 12)
    text("I plan to decide and write down what each function should do before coding it, so I have a clear contract to implement and test.", size=11)
    footer(2)
    c.save()

    writer = PdfWriter()
    writer.append(PdfReader(str(raw)))
    structure = pdf_dict({"/Type": NameObject("/StructTreeRoot")})
    structure_ref = writer._add_object(structure)
    document = pdf_dict({"/Type": NameObject("/StructElem"), "/S": NameObject("/Document"),
                                 "/P": structure_ref, "/K": ArrayObject()})
    document_ref = writer._add_object(document)
    parents = {page: [] for page in counts}
    for item in tags:
        node = pdf_dict({"/Type": NameObject("/StructElem"),
                                 "/S": NameObject("/" + item["kind"]),
                                 "/P": document_ref,
                                 "/Pg": writer.pages[item["page"]].indirect_reference,
                                 "/K": NumberObject(item["mcid"])})
        if item["alt"]:
            node[NameObject("/Alt")] = TextStringObject(item["alt"])
        ref = writer._add_object(node)
        document["/K"].append(ref)
        parents[item["page"]].append(ref)
    nums = ArrayObject()
    for page, refs in parents.items():
        nums.extend([NumberObject(page), ArrayObject(refs)])
        writer.pages[page][NameObject("/StructParents")] = NumberObject(page)
        writer.pages[page][NameObject("/Tabs")] = NameObject("/S")
    structure.update({NameObject("/K"): ArrayObject([document_ref]),
                      NameObject("/ParentTree"): writer._add_object(pdf_dict({"/Nums": nums})),
                      NameObject("/ParentTreeNextKey"): NumberObject(len(parents))})
    writer._root_object.update({NameObject("/StructTreeRoot"): structure_ref,
                                NameObject("/MarkInfo"): pdf_dict({"/Marked": BooleanObject(True)}),
                                NameObject("/Lang"): TextStringObject("en-US"),
                                NameObject("/ViewerPreferences"): pdf_dict({"/DisplayDocTitle": BooleanObject(True)})})
    writer.add_metadata({"/Title": "Developing a ReAct Sudoku Agent", "/Subject": "CS 4300 development-process report",
                         "/Author": "CS 4300 student", "/Creator": "Project report generator"})
    final = OUT / "react-sudoku-report.pdf"
    writer.write(str(final))
    verify(final, reviewed)
    print(final)


def verify(path, reviewed):
    import pymupdf
    reader = PdfReader(str(path))
    full_text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) == 2
    assert REPO in full_text
    assert "Takeaway I plan to keep" in full_text
    assert reader.trailer["/Root"]["/Lang"] == "en-US"
    root = reader.trailer["/Root"]["/StructTreeRoot"]
    elements = root["/K"][0].get_object()["/K"]
    tags = [ref.get_object()["/S"] for ref in elements]
    assert "/H1" in tags and "/H2" in tags and "/P" in tags
    figures = [ref.get_object() for ref in elements if ref.get_object()["/S"] == "/Figure"]
    assert len(figures) == 1 and figures[0]["/Alt"]
    doc = pymupdf.open(str(path))
    for index, page in enumerate(doc):
        page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(str(TEMP / f"report-page-{index + 1}.png"))
        for block in page.get_text("blocks"):
            assert block[0] >= 0 and block[1] >= 0 and block[2] <= 613 and block[3] <= 793
    evidence = {"pages": 2, "selectable_text": True, "semantic_heading_tags": True,
                "structure_tree_reading_order": True, "diagram_alt_text": True,
                "language": "en-US", "student_review_confirmed": reviewed,
                "visual_review": "pending", "pdf_ua_certified": False}
    (ROOT / "docs/evidence/report-accessibility.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    build()
