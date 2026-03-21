"""Variation Order PDF generator — Imperial Homes branded A4 document."""

import logging
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"
_BR, _BG, _BB = 180, 37, 65
_LR, _LG, _LB = 250, 242, 244
_GR, _GG, _GB = 245, 245, 245

_STATUS_COLOURS = {
    "approved":    (34, 139, 34),
    "implemented": (34, 139, 34),
    "submitted":   (30, 144, 255),
    "under_review":(255, 165, 0),
    "rejected":    (200, 50, 50),
    "draft":       (120, 120, 120),
    "cancelled":   (120, 120, 120),
}


def generate_variation_order_pdf(
    *,
    variation_number: str,
    title: str,
    variation_type: str,
    status: str,
    requested_date: date,
    priority: str = "medium",
    currency: str = "GHS",
    # Project
    project_name: str,
    project_code: str = "",
    project_location: str = "",
    # Parties
    client_name: str = "",
    contractor_name: str = "",
    # Financial impact
    original_amount: float = 0.0,
    variation_amount: float = 0.0,
    new_total_amount: float = 0.0,
    # Time impact
    impact_on_timeline: int = 0,
    original_completion_date: Optional[date] = None,
    new_completion_date: Optional[date] = None,
    # Narrative
    description: str = "",
    justification: str = "",
    impact_assessment: str = "",
    # Approval
    approved_date: Optional[date] = None,
    rejection_reason: str = "",
) -> bytes:
    """Return a Variation Order PDF as raw bytes."""
    try:
        from fpdf import FPDF
    except ImportError:
        logger.error("fpdf2 not installed")
        return b""

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    W = pdf.w - pdf.l_margin - pdf.r_margin
    lm = pdf.l_margin

    # ── Header band ───────────────────────────────────────────────────────────
    pdf.set_fill_color(_BR, _BG, _BB)
    pdf.rect(lm, 10, W, 30, style="F")
    if _LOGO_PATH.exists():
        try:
            pdf.image(str(_LOGO_PATH), x=lm + 3, y=12, h=24)
        except Exception:
            pass
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(lm + 35, 13)
    pdf.cell(W - 35, 8, "IMPERIAL HOMES LIMITED")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(lm + 35, 21)
    pdf.cell(W - 35, 5, "P.O. Box 7451, Accra North  |  Tel: +233 302 731 033  |  www.imperialhomesghana.com")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(lm, 30)
    pdf.cell(W, 7, "VARIATION ORDER", align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(44)

    # ── Reference band ────────────────────────────────────────────────────────
    ref_y = pdf.get_y() + 2
    pdf.set_fill_color(_LR, _LG, _LB)
    pdf.rect(lm, ref_y, W, 9, style="F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(_BR, _BG, _BB)
    pdf.set_xy(lm + 2, ref_y + 1.5)
    pdf.cell(38, 6, f"VO No:  {variation_number}")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(42, 6, f"Type: {variation_type.replace('_', ' ').title()}")
    pdf.cell(40, 6, f"Date: {requested_date.strftime('%d %b %Y')}")
    # Status pill
    sr, sg, sb = _STATUS_COLOURS.get(status, (100, 100, 100))
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(sr, sg, sb)
    pdf.cell(30, 6, status.replace("_", " ").upper())
    # Priority
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, f"Priority: {priority.upper()}")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(ref_y + 13)

    # ── Title bar ─────────────────────────────────────────────────────────────
    title_y = pdf.get_y()
    pdf.set_fill_color(_GR, _GG, _GB)
    pdf.rect(lm, title_y, W, 9, style="F")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(lm + 3, title_y + 1)
    pdf.cell(W - 6, 7, title)
    pdf.ln(12)

    def _sbar(t):
        y = pdf.get_y()
        pdf.set_fill_color(_BR, _BG, _BB)
        pdf.rect(lm, y, W, 7, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(lm + 2, y + 0.5)
        pdf.cell(W - 4, 6, t)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

    def _irow(l1, v1, l2="", v2=""):
        col = W / 2
        y = pdf.get_y()
        pdf.set_fill_color(_GR, _GG, _GB)
        pdf.rect(lm, y, W, 6.5, style="F")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(lm + 2, y + 0.5)
        pdf.cell(32, 5.5, l1 + ":")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(col - 36, 5.5, v1)
        if l2:
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(32, 5.5, l2 + ":")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5.5, v2)
        pdf.ln(7)

    # ── Project & parties ─────────────────────────────────────────────────────
    _sbar("PROJECT DETAILS")
    _irow("Project Name", project_name, "Project Code", project_code)
    if project_location:
        _irow("Location", project_location)
    _irow("Client", client_name or "—", "Contractor", contractor_name or "—")
    pdf.ln(2)

    # ── Financial impact ──────────────────────────────────────────────────────
    _sbar("FINANCIAL IMPACT")

    fin_headers = ["Item", "Amount"]
    fin_w = [W - 4 - 45, 45]
    fin_rows = [
        ["Original Contract Value", f"{currency}  {original_amount:,.2f}"],
        ["Variation Amount", f"{currency}  {variation_amount:+,.2f}"],
        ["Revised Contract Value", f"{currency}  {new_total_amount:,.2f}"],
    ]
    y = pdf.get_y()
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(lm, y, W, 6.5, style="F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(lm + 2, y + 0.5)
    pdf.cell(fin_w[0], 5.5, "Item")
    pdf.cell(fin_w[1], 5.5, "Amount", align="R")
    pdf.ln(7)

    for idx, (label, amt) in enumerate(fin_rows):
        y = pdf.get_y()
        bold = idx == 2
        if bold:
            pdf.set_fill_color(_LR, _LG, _LB)
            pdf.rect(lm, y, W, 7, style="F")
        pdf.set_font("Helvetica", "B" if bold else "", 9)
        pdf.set_xy(lm + 4, y + 0.8)
        pdf.cell(fin_w[0] - 4, 5.5, label)
        pdf.cell(fin_w[1], 5.5, amt, align="R")
        pdf.ln(7.5)

    pdf.ln(2)

    # ── Time impact ───────────────────────────────────────────────────────────
    if impact_on_timeline or original_completion_date or new_completion_date:
        _sbar("TIME IMPACT")
        _irow("Timeline Impact", f"{impact_on_timeline:+d} days" if impact_on_timeline else "None")
        if original_completion_date:
            _irow(
                "Original Completion",
                original_completion_date.strftime("%d %b %Y"),
                "Revised Completion",
                new_completion_date.strftime("%d %b %Y") if new_completion_date else "—",
            )
        pdf.ln(2)

    # ── Narrative ─────────────────────────────────────────────────────────────
    for section, text in [
        ("DESCRIPTION OF VARIATION", description),
        ("JUSTIFICATION", justification),
        ("IMPACT ASSESSMENT", impact_assessment),
    ]:
        if text:
            _sbar(section)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_x(lm + 2)
            pdf.multi_cell(W - 4, 5.5, text.strip())
            pdf.ln(2)

    if rejection_reason:
        _sbar("REJECTION REASON")
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, rejection_reason.strip())
        pdf.ln(2)

    # ── Approval ─────────────────────────────────────────────────────────────
    _sbar("APPROVAL & SIGN-OFF")
    pdf.ln(2)
    sig_w = (W - 8) / 3
    sig_y = pdf.get_y()
    for i, (role, name_hint) in enumerate([
        ("Prepared By", "Project Manager"),
        ("Approved By", "Client / Employer"),
        ("Acknowledged By", contractor_name or "Contractor"),
    ]):
        x = lm + i * (sig_w + 4)
        if i == 1 and approved_date:
            pdf.set_font("Helvetica", "", 7)
            pdf.set_xy(x + 2, sig_y)
            pdf.cell(sig_w - 4, 4, f"Date: {approved_date.strftime('%d %b %Y')}")
        pdf.set_draw_color(160, 160, 160)
        pdf.line(x + 2, sig_y + 16, x + sig_w - 2, sig_y + 16)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(x + 2, sig_y + 17)
        pdf.cell(sig_w - 4, 5, role)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, sig_y + 22)
        pdf.cell(sig_w - 4, 5, name_hint)

    pdf.set_y(sig_y + 30)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-18)
    pdf.set_draw_color(_BR, _BG, _BB)
    pdf.set_line_width(0.5)
    pdf.line(lm, pdf.get_y(), lm + W, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.set_x(lm)
    pdf.cell(W / 2, 4, "IMPERIAL HOMES LIMITED  •  CONFIDENTIAL")
    pdf.cell(W / 2, 4, f"VO: {variation_number}  |  Generated: {date.today().strftime('%d %b %Y')}", align="R")

    return bytes(pdf.output())
