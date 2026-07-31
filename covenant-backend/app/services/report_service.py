"""
Module: Contract Analysis Report Export.

Generates a downloadable PDF summarizing everything the platform extracted
and inferred about a contract: metadata, executive summary, key risk
flags, a full clause-by-clause breakdown (type, ML confidence, risk
score), and compliance audit results if one has been run. This is the
"give me a document I can actually hand to someone" output — everything
else in the app is for working inside the tool; this is for taking
findings outside it.

Uses reportlab (no external binaries required, works the same on Windows/
Mac/Linux, unlike HTML-to-PDF converters that need a browser engine).
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
                                 Spacer, Table, TableStyle)

INK = colors.HexColor("#14213D")
SLATE = colors.HexColor("#5B6478")
BRASS = colors.HexColor("#A9822E")
REDLINE = colors.HexColor("#B3271E")
AMBER = colors.HexColor("#B8862E")
GREEN = colors.HexColor("#2F7A52")
LINE = colors.HexColor("#E4E2DB")
PAPER = colors.HexColor("#F7F7F4")


def _severity_color(severity: str):
    return {"high": REDLINE, "medium": AMBER, "low": GREEN}.get(severity, SLATE)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportTitle", fontName="Helvetica-Bold", fontSize=20, textColor=INK, spaceAfter=4))
    styles.add(ParagraphStyle("ReportSubtitle", fontName="Helvetica", fontSize=10, textColor=SLATE, spaceAfter=14))
    styles.add(ParagraphStyle("SectionHeading", fontName="Helvetica-Bold", fontSize=13, textColor=INK,
                               spaceBefore=16, spaceAfter=8))
    styles.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#2A2A2A"),
                               leading=14))
    styles.add(ParagraphStyle("Meta", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=13))
    styles.add(ParagraphStyle("MetaLabel", fontName="Helvetica-Bold", fontSize=8, textColor=SLATE))
    styles.add(ParagraphStyle("ClauseHeading", fontName="Helvetica-Bold", fontSize=10, textColor=INK, spaceBefore=10))
    styles.add(ParagraphStyle("ClauseMeta", fontName="Helvetica", fontSize=8, textColor=SLATE, spaceAfter=4))
    styles.add(ParagraphStyle("Footer", fontName="Helvetica", fontSize=7.5, textColor=SLATE))
    return styles


def _header_footer(canvas, doc, contract_title: str):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(20 * mm, 12 * mm, f"Covenant AI Legal Copilot - {contract_title}")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


def generate_contract_report_pdf(contract, compliance_results=None) -> bytes:
    """
    contract: app.db.models.Contract instance (with .clauses loaded)
    compliance_results: optional list of app.db.models.ComplianceResult,
        with an accompanying rule-name lookup already resolved into each
        item as `.rule_name` / `.status` / `.reasoning` (see the route).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"{contract.display_code} - Contract Analysis Report",
    )
    styles = _build_styles()
    story = []

    # --- Title block ---
    story.append(Paragraph("Contract Analysis Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"{contract.display_code} &middot; Generated {datetime.utcnow().strftime('%B %d, %Y')} by Covenant AI Legal Copilot",
        styles["ReportSubtitle"],
    ))
    story.append(Paragraph(contract.title, ParagraphStyle(
        "ContractTitle", fontName="Helvetica-Bold", fontSize=14, textColor=INK, spaceAfter=10,
    )))

    # --- Risk score + status banner ---
    risk = contract.risk_score
    risk_label = "High Risk" if risk >= 61 else "Medium Risk" if risk >= 31 else "Low Risk"
    risk_color = _severity_color("high" if risk >= 61 else "medium" if risk >= 31 else "low")
    banner_data = [[
        Paragraph(f"<b>Overall Risk Score</b><br/><font size=16 color='{risk_color.hexval()}'>{risk}/100</font> "
                  f"<font size=9 color='{risk_color.hexval()}'>{risk_label}</font>", styles["Body"]),
        Paragraph(f"<b>Status</b><br/>{contract.status.value.replace('_', ' ').title()}", styles["Body"]),
        Paragraph(f"<b>Clauses Extracted</b><br/>{len(contract.clauses)}", styles["Body"]),
    ]]
    banner = Table(banner_data, colWidths=[57 * mm, 57 * mm, 57 * mm])
    banner.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 14))

    # --- Metadata table ---
    story.append(Paragraph("Contract Details", styles["SectionHeading"]))
    meta_rows = [
        ("Effective Date", contract.effective_date or "\u2014"),
        ("Expiry Date", contract.expiry_date or "\u2014"),
        ("Governing Law", contract.governing_law or "\u2014"),
        ("Payment Terms", contract.payment_terms or "\u2014"),
        ("Parties", ", ".join(contract.parties) if contract.parties else "\u2014"),
        ("Pages", str(contract.page_count)),
    ]
    meta_table_data = [[Paragraph(f"<b>{k}</b>", styles["MetaLabel"]), Paragraph(v, styles["Meta"])] for k, v in meta_rows]
    meta_table = Table(meta_table_data, colWidths=[38 * mm, 133 * mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)

    # --- Executive summary ---
    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    story.append(Paragraph(contract.executive_summary or "No summary was generated for this contract.", styles["Body"]))

    # --- Key risk flags ---
    all_flags = [(cl, f) for cl in contract.clauses for f in cl.risk_flags]
    story.append(Paragraph("Key Risk Flags", styles["SectionHeading"]))
    if all_flags:
        flag_rows = [[
            Paragraph("<b>Severity</b>", styles["MetaLabel"]),
            Paragraph("<b>Clause</b>", styles["MetaLabel"]),
            Paragraph("<b>Finding</b>", styles["MetaLabel"]),
        ]]
        for cl, f in sorted(all_flags, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x[1].severity.value]):
            sev_color = _severity_color(f.severity.value)
            flag_rows.append([
                Paragraph(f"<font color='{sev_color.hexval()}'><b>{f.severity.value.upper()}</b></font>", styles["Body"]),
                Paragraph(f"&sect;{cl.clause_number}", styles["Body"]),
                Paragraph(f.reason, styles["Body"]),
            ])
        flag_table = Table(flag_rows, colWidths=[20 * mm, 20 * mm, 131 * mm], repeatRows=1)
        flag_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF0F3")),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(flag_table)
    else:
        story.append(Paragraph("No risk flags were raised for this contract.", styles["Body"]))

    # --- Compliance results ---
    if compliance_results:
        story.append(Paragraph("Compliance Audit", styles["SectionHeading"]))
        comp_rows = [[
            Paragraph("<b>Rule</b>", styles["MetaLabel"]),
            Paragraph("<b>Status</b>", styles["MetaLabel"]),
            Paragraph("<b>Reasoning</b>", styles["MetaLabel"]),
        ]]
        status_color_map = {"compliant": GREEN, "non_compliant": REDLINE, "needs_review": AMBER}
        for r in compliance_results:
            c = status_color_map.get(r.status, SLATE)
            comp_rows.append([
                Paragraph(r.rule_name, styles["Body"]),
                Paragraph(f"<font color='{c.hexval()}'><b>{r.status.replace('_', ' ').title()}</b></font>", styles["Body"]),
                Paragraph(r.reasoning, styles["Body"]),
            ])
        comp_table = Table(comp_rows, colWidths=[45 * mm, 26 * mm, 100 * mm], repeatRows=1)
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF0F3")),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(comp_table)

    # --- Full clause-by-clause breakdown ---
    story.append(PageBreak())
    story.append(Paragraph("Clause-by-Clause Breakdown", styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", color=LINE, thickness=0.75, spaceAfter=8))

    for cl in sorted(contract.clauses, key=lambda c: c.clause_number):
        sev_color = _severity_color(cl.risk_severity.value)
        story.append(Paragraph(
            f"&sect;{cl.clause_number} &mdash; {cl.clause_type.replace('_', ' ')}",
            styles["ClauseHeading"],
        ))
        story.append(Paragraph(
            f"Classification confidence: {cl.classification_confidence}% &middot; "
            f"Risk score: <font color='{sev_color.hexval()}'><b>{cl.risk_score}</b></font> "
            f"({cl.risk_severity.value})",
            styles["ClauseMeta"],
        ))
        story.append(Paragraph(cl.text, styles["Body"]))
        if cl.risk_flags:
            for f in cl.risk_flags:
                fc = _severity_color(f.severity.value)
                story.append(Paragraph(
                    f"&#8226; <font color='{fc.hexval()}'>[{f.severity.value.upper()}]</font> {f.reason}",
                    styles["Meta"],
                ))

    def _on_page(canvas, doc_):
        _header_footer(canvas, doc_, contract.display_code)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
