import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from backend.core.config import get_settings
from backend.core.logging import get_logger


# Reportlab's default fonts (Helvetica) are Latin-1 only.
# Replace common non-Latin-1 chars so the PDF doesn't crash.
_CHAR_MAP = {
    "\u20b9": "Rs.",   # ₹ Indian Rupee
    "\u20ac": "EUR",   # €
    "\u00a3": "GBP",   # £
    "\u00a5": "JPY",   # ¥
    "\u2019": "'",     # right single quote
    "\u2018": "'",     # left single quote
    "\u201c": '"',     # left double quote
    "\u201d": '"',     # right double quote
    "\u2013": "-",     # en dash
    "\u2014": "--",    # em dash
    "\u2022": "*",     # bullet
    "\u00ae": "(R)",   # ®
    "\u2122": "(TM)",  # ™
}

def _safe(text: str) -> str:
    if not text:
        return text
    for ch, repl in _CHAR_MAP.items():
        text = text.replace(ch, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")

logger = get_logger(__name__)
settings = get_settings()

# ── Color Palette ─────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#1a237e")
ACCENT = colors.HexColor("#0288d1")
LIGHT_BG = colors.HexColor("#e3f2fd")
SUCCESS = colors.HexColor("#2e7d32")
WARNING = colors.HexColor("#f57c00")
DANGER = colors.HexColor("#c62828")
NEUTRAL = colors.HexColor("#455a64")
LIGHT_GREY = colors.HexColor("#f5f5f5")
WHITE = colors.white
BLACK = colors.black


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontSize=28, textColor=WHITE, alignment=TA_CENTER, spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base["Normal"],
            fontSize=13, textColor=colors.HexColor("#bbdefb"), alignment=TA_CENTER, spaceAfter=6,
        ),
        "section_header": ParagraphStyle(
            "section_header", parent=base["Heading1"],
            fontSize=16, textColor=PRIMARY, spaceBefore=18, spaceAfter=8,
            borderPad=4,
        ),
        "sub_header": ParagraphStyle(
            "sub_header", parent=base["Heading2"],
            fontSize=12, textColor=ACCENT, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, textColor=BLACK, leading=15, alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontSize=10, textColor=NEUTRAL, leading=14,
            leftIndent=16, spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8, textColor=NEUTRAL, alignment=TA_CENTER,
        ),
    }
    return {**base.byName, **custom}


def _divider(width=480):
    return HRFlowable(width=width, thickness=1, color=ACCENT, spaceAfter=8, spaceBefore=4)


def _data_source_banner(story, styles, data_source: str):
    if "uploaded" in data_source:
        label = "Data Source: Uploaded Documents"
        note = ("This report is grounded in the documents you uploaded. "
                "Figures and claims are drawn directly from those sources.")
        bg = colors.HexColor("#e8f5e9")
        border = SUCCESS
    else:
        label = "Data Source: Web Search + LLM Knowledge"
        note = ("This report uses live web search results combined with AI knowledge. "
                "Key figures (market size, CAGR, revenue) are estimates — "
                "please verify critical numbers with primary sources before making business decisions.")
        bg = colors.HexColor("#fff3e0")
        border = WARNING

    banner_data = [[
        Paragraph(f"<b>{_safe(label)}</b>", ParagraphStyle(
            "ds_label", fontSize=11, textColor=BLACK, spaceAfter=4,
        )),
    ], [
        Paragraph(_safe(note), ParagraphStyle(
            "ds_note", fontSize=9, textColor=NEUTRAL, leading=13,
        )),
    ]]
    banner = Table(banner_data, colWidths=[480])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1.5, border),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))


def _cover_page(story, styles, topic: str, date_str: str):
    # Blue header block simulated with a table
    header_data = [[
        Paragraph(f"AI Market Research Report", styles["cover_title"]),
    ]]
    header_table = Table(header_data, colWidths=[480])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 40),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 40),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 24))

    topic_data = [[Paragraph(topic, ParagraphStyle(
        "t", fontSize=20, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=8
    ))]]
    topic_table = Table(topic_data, colWidths=[480])
    topic_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("BOX", (0, 0), (-1, -1), 1.5, ACCENT),
    ]))
    story.append(topic_table)
    story.append(Spacer(1, 20))

    meta = [
        ["Generated by", "AI Market Research Copilot"],
        ["Date", date_str],
        ["Powered by", "NVIDIA NIM  ·  FAISS  ·  RAG Pipeline"],
    ]
    meta_table = Table(meta, colWidths=[140, 340])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), NEUTRAL),
        ("TEXTCOLOR", (1, 0), (1, -1), BLACK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(PageBreak())


def _section(story, styles, title: str, content: str):
    story.append(Paragraph(_safe(title), styles["section_header"]))
    story.append(_divider())
    for para in _safe(content).split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), styles["body"]))
    story.append(Spacer(1, 10))


def _competitors_section(story, styles, competitors: list):
    story.append(Paragraph("Competitive Landscape", styles["section_header"]))
    story.append(_divider())

    for comp in competitors:
        name = _safe(comp.get("name", "Unknown"))
        desc = _safe(comp.get("description", ""))
        position = _safe(comp.get("market_position", ""))
        strengths = comp.get("strengths", [])
        weaknesses = comp.get("weaknesses", [])

        pos_color = {"Leader": SUCCESS, "Challenger": ACCENT, "Niche": WARNING}.get(position, NEUTRAL)

        # Competitor header row
        header_data = [[
            Paragraph(f"<b>{name}</b>", ParagraphStyle("ch", fontSize=12, textColor=WHITE)),
            Paragraph(position, ParagraphStyle("cp", fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
        ]]
        comp_header = Table(header_data, colWidths=[360, 120])
        comp_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), PRIMARY),
            ("BACKGROUND", (1, 0), (1, 0), pos_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(comp_header)

        # Description + S/W
        sw_data = [
            [
                Paragraph(f"<b>Strengths</b>", styles["sub_header"]),
                Paragraph(f"<b>Weaknesses</b>", styles["sub_header"]),
            ],
            [
                Paragraph("\n".join(f"* {_safe(s)}" for s in strengths) or "N/A", styles["bullet"]),
                Paragraph("\n".join(f"* {_safe(w)}" for w in weaknesses) or "N/A", styles["bullet"]),
            ],
        ]
        sw_table = Table(sw_data, colWidths=[240, 240])
        sw_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(sw_table)
        if desc:
            story.append(Paragraph(desc, styles["body"]))
        story.append(Spacer(1, 12))


def _pricing_section(story, styles, pricing: list):
    story.append(Paragraph("Pricing Intelligence", styles["section_header"]))
    story.append(_divider())

    header = [["Segment", "Price Range", "Key Players", "Insights"]]
    rows = []
    for p in pricing:
        rows.append([
            Paragraph(_safe(p.get("segment", "")), styles["bullet"]),
            Paragraph(_safe(p.get("price_range", "")), styles["bullet"]),
            Paragraph(_safe(", ".join(p.get("key_players", []))), styles["bullet"]),
            Paragraph(_safe(p.get("notes", "")), styles["bullet"]),
        ])

    table_data = header + rows
    price_table = Table(table_data, colWidths=[100, 110, 120, 150])
    price_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(price_table)
    story.append(Spacer(1, 10))


def _trends_section(story, styles, trends: list):
    story.append(Paragraph("Market Trends", styles["section_header"]))
    story.append(_divider())

    impact_colors = {"High": DANGER, "Medium": WARNING, "Low": SUCCESS}

    for i, trend in enumerate(trends, 1):
        impact = trend.get("impact", "Medium")
        i_color = impact_colors.get(impact, NEUTRAL)

        row = [[
            Paragraph(f"<b>{i}. {_safe(trend.get('trend', ''))}</b>", styles["sub_header"]),
            Paragraph(_safe(impact), ParagraphStyle("imp", fontSize=9, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(_safe(trend.get("timeframe", "")), ParagraphStyle("tf", fontSize=9, textColor=NEUTRAL, alignment=TA_CENTER)),
        ]]
        t = Table(row, colWidths=[310, 80, 90])
        t.setStyle(TableStyle([
            ("BACKGROUND", (1, 0), (1, 0), i_color),
            ("BACKGROUND", (2, 0), (2, 0), LIGHT_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(t)
        story.append(Paragraph(_safe(trend.get("description", "")), styles["body"]))
        story.append(Spacer(1, 6))


def _swot_section(story, styles, swot: dict):
    story.append(Paragraph("SWOT Analysis", styles["section_header"]))
    story.append(_divider())

    def _cell(title, items, bg):
        content = f"<b>{_safe(title)}</b><br/><br/>" + "<br/>".join(f"* {_safe(i)}" for i in items)
        return Paragraph(content, ParagraphStyle(
            "swot_cell", fontSize=10, textColor=BLACK, leading=15,
        ))

    swot_data = [[
        _cell("Strengths", swot.get("strengths", []), SUCCESS),
        _cell("Weaknesses", swot.get("weaknesses", []), DANGER),
    ], [
        _cell("Opportunities", swot.get("opportunities", []), ACCENT),
        _cell("Threats", swot.get("threats", []), WARNING),
    ]]

    swot_table = Table(swot_data, colWidths=[240, 240])
    swot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e8f5e9")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#ffebee")),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#e3f2fd")),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#fff3e0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(swot_table)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf_report(
    session_id: str,
    topic: str,
    executive_summary: str,
    competitors: list,
    pricing_insights: list,
    market_trends: list,
    swot_analysis: dict,
    data_source: str = "web_search+llm",
) -> Path:
    """Build a full PDF report and return the file path."""
    filename = f"report_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = settings.REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Market Research Report – {topic}",
        author="AI Market Research Copilot",
    )

    styles = _styles()
    story = []
    date_str = datetime.now().strftime("%B %d, %Y")

    # Cover
    _cover_page(story, styles, topic, date_str)

    # Data source disclaimer
    _data_source_banner(story, styles, data_source)

    # Table of Contents (static)
    story.append(Paragraph("Table of Contents", styles["section_header"]))
    story.append(_divider())
    toc_items = [
        "1. Executive Summary",
        "2. Competitive Landscape",
        "3. Pricing Intelligence",
        "4. Market Trends",
        "5. SWOT Analysis",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["bullet"]))
    story.append(PageBreak())

    # Sections
    _section(story, styles, "1. Executive Summary", executive_summary)
    story.append(PageBreak())

    _competitors_section(story, styles, competitors)
    story.append(PageBreak())

    _pricing_section(story, styles, pricing_insights)
    story.append(PageBreak())

    _trends_section(story, styles, market_trends)
    story.append(PageBreak())

    _swot_section(story, styles, swot_analysis)

    # Footer note
    story.append(Spacer(1, 30))
    story.append(_divider())
    story.append(Paragraph(
        "Generated by AI Market Research Copilot · Powered by NVIDIA NIM · FAISS RAG Pipeline",
        styles["caption"],
    ))

    doc.build(story)
    logger.info(f"PDF report saved: {output_path}")
    return output_path
