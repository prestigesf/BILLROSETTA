"""Bundle README + all source files into a single printable PDF."""
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted,
)

ROOT = Path(__file__).parent
OUT = Path.home() / "OneDrive" / "Desktop" / "BillRosetta-Moss-Bridge.pdf"

FILES = [
    ("README.md", "README"),
    ("main.py", "main.py — FastAPI app"),
    ("server.py", "server.py — MCP server (stdio)"),
    ("brightdata.py", "brightdata.py — Web Unlocker client"),
    ("verify_16_run.py", "verify_16_run.py — pytest smoke test"),
    ("verify_mcp.py", "verify_mcp.py — MCP client session test"),
    ("test_server.py", "test_server.py — MCP tool import test"),
    ("test_brightdata.py", "test_brightdata.py — scraper tests"),
    ("requirements.txt", "requirements.txt"),
    ("pyproject.toml", "pyproject.toml"),
]

styles = getSampleStyleSheet()
h1 = styles["Heading1"]
h2 = ParagraphStyle("h2", parent=styles["Heading2"], spaceBefore=6, spaceAfter=6)
body = styles["BodyText"]
code = ParagraphStyle(
    "code", parent=styles["Code"], fontName="Courier", fontSize=8.5,
    leading=10.5, alignment=TA_LEFT, textColor="#111",
)

doc = SimpleDocTemplate(
    str(OUT), pagesize=LETTER,
    leftMargin=0.6*inch, rightMargin=0.6*inch,
    topMargin=0.6*inch, bottomMargin=0.6*inch,
    title="BillRosetta Moss Bridge",
)

story = [
    Paragraph("BillRosetta Moss Bridge", h1),
    Paragraph("Hackathon submission — Moss + Bright Data. PrestigeSF · Nicholle Simon.", body),
    Paragraph(f"Project path: {ROOT}", body),
    Spacer(1, 0.15*inch),
]

for fname, title in FILES:
    p = ROOT / fname
    story.append(Paragraph(title, h2))
    text = p.read_text(encoding="utf-8") if p.exists() else "(missing)"
    story.append(Preformatted(text, code))
    story.append(PageBreak())

doc.build(story[:-1])  # drop trailing PageBreak
print(f"WROTE: {OUT}")
