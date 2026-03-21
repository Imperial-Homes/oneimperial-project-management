"""Payment Certificate PDF generator — Imperial Homes branded A4 document."""

import logging
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"

# Imperial Homes brand colour #B42541
_BR, _BG, _BB = 180, 37, 65
_LIGHT_R, _LIGHT_G, _LIGHT_B = 250, 242, 244   # very light red tint
_GREY_R, _GREY_G, _GREY_B = 245, 245, 245


def generate_payment_certificate_pdf(
    *,
    # Certificate meta
    certificate_number: str,
    certificate_type: str,           # "Interim" / "Final" / "Advance" / "Retention" / "Variation"
    certificate_date: date,
    status: str,
    currency: str = "GHS",
    # Project
    project_name: str,
    project_code: str,
    project_location: str = "",
    project_type: str = "",
    # Parties
    client_name: str = "",
    contractor_name: str = "",
    consultant_name: str = "",
    # Work period
    period_from: Optional[date] = None,
    period_to: Optional[date] = None,
    # Financial summary
    gross_amount: float = 0.0,
    previous_amount: float = 0.0,
    current_amount: float = 0.0,
    retention_percentage: float = 5.0,
    retention_amount: float = 0.0,
    net_amount: float = 0.0,
    # Work description
    work_completed: str = "",
    description: str = "",
    notes: str = "",
    # Approval
    submitted_date: Optional[date] = None,
    approved_date: Optional[date] = None,
    payment_date: Optional[date] = None,
    payment_reference: str = "",
    amount_paid: float = 0.0,
) -> bytes:
    """Return an A4 Payment Certificate PDF as raw bytes."""
    try:
        from fpdf import FPDF
    except ImportError:
        logger.error("fpdf2 is not installed — cannot generate payment certificate PDF")
        return b""

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    W = pdf.w - pdf.l_margin - pdf.r_margin   # usable width ≈ 190 mm
    lm = pdf.l_margin

    # ─────────────────────────────────────────────────────────────────────────
    # HEADER BAND
    # ─────────────────────────────────────────────────────────────────────────
    header_h = 30
    pdf.set_fill_color(_BR, _BG, _BB)
    pdf.rect(lm, 10, W, header_h, style="F")

    # Logo
    if _LOGO_PATH.exists():
        try:
            pdf.image(str(_LOGO_PATH), x=lm + 3, y=12, h=24)
        except Exception:
            pass

    # Company name & address block
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(lm + 35, 13)
    pdf.cell(W - 35, 8, "IMPERIAL HOMES LIMITED")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(lm + 35, 21)
    pdf.cell(W - 35, 5, "P.O. Box 7451, Accra North  |  Tel: +233 302 731 033  |  www.imperialhomesghana.com")

    # Document title on the right
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(lm, 31)
    pdf.cell(W, 7, "PAYMENT CERTIFICATE", align="R")

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(10 + header_h + 4)

    # ─────────────────────────────────────────────────────────────────────────
    # CERTIFICATE REFERENCE BAND (coloured pill row)
    # ─────────────────────────────────────────────────────────────────────────
    ref_y = pdf.get_y()
    pdf.set_fill_color(_LIGHT_R, _LIGHT_G, _LIGHT_B)
    pdf.rect(lm, ref_y, W, 9, style="F")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(_BR, _BG, _BB)
    pdf.set_xy(lm + 2, ref_y + 1.5)
    pdf.cell(50, 6, f"Certificate No:  {certificate_number}")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(lm + 65, ref_y + 1.5)
    pdf.cell(45, 6, f"Type: {certificate_type.upper()}")
    pdf.set_xy(lm + 115, ref_y + 1.5)
    pdf.cell(40, 6, f"Date: {certificate_date.strftime('%d %B %Y')}")
    pdf.set_xy(lm + 160, ref_y + 1.5)
    status_label = status.replace("_", " ").upper()
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(_BR, _BG, _BB)
    pdf.cell(0, 6, status_label)

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(ref_y + 12)

    # ─────────────────────────────────────────────────────────────────────────
    # PROJECT & PARTIES  (two-column info grid)
    # ─────────────────────────────────────────────────────────────────────────
    def _section_bar(title: str) -> None:
        y = pdf.get_y()
        pdf.set_fill_color(_BR, _BG, _BB)
        pdf.rect(lm, y, W, 7, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(lm + 2, y + 0.5)
        pdf.cell(W - 4, 6, title)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

    def _info_row(
        label1: str, val1: str,
        label2: str = "", val2: str = "",
    ) -> None:
        col = W / 2
        y = pdf.get_y()
        pdf.set_fill_color(_GREY_R, _GREY_G, _GREY_B)
        pdf.rect(lm, y, W, 6.5, style="F")

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(lm + 2, y + 0.5)
        pdf.cell(30, 5.5, label1 + ":", border=0)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(col - 34, 5.5, val1, border=0)

        if label2:
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(30, 5.5, label2 + ":", border=0)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5.5, val2, border=0)

        pdf.ln(7)

    _section_bar("PROJECT DETAILS")
    _info_row("Project Name", project_name, "Project Code", project_code)
    _info_row("Location", project_location, "Project Type", project_type.replace("_", " ").title())
    if period_from and period_to:
        _info_row(
            "Work Period",
            f"{period_from.strftime('%d %b %Y')} — {period_to.strftime('%d %b %Y')}",
        )
    pdf.ln(2)

    _section_bar("PARTIES")
    _info_row("Client", client_name, "Contractor", contractor_name)
    _info_row("Consultant", consultant_name or "Imperial Homes Ltd")
    pdf.ln(2)

    # ─────────────────────────────────────────────────────────────────────────
    # FINANCIAL SUMMARY TABLE
    # ─────────────────────────────────────────────────────────────────────────
    _section_bar("FINANCIAL SUMMARY")

    def _fin_row(label: str, amount: float, bold: bool = False, highlight: bool = False) -> None:
        y = pdf.get_y()
        if highlight:
            pdf.set_fill_color(_LIGHT_R, _LIGHT_G, _LIGHT_B)
            pdf.rect(lm, y, W, 7, style="F")
        style = "B" if bold else ""
        pdf.set_font("Helvetica", style, 9)
        pdf.set_xy(lm + 4, y + 0.8)
        pdf.cell(W - 50, 5.5, label, border=0)
        amount_str = f"{currency}  {amount:>15,.2f}"
        pdf.set_font("Helvetica", style, 9)
        pdf.cell(46, 5.5, amount_str, align="R", border=0)
        pdf.ln(7.5)

    def _fin_divider() -> None:
        y = pdf.get_y() - 1
        pdf.set_draw_color(200, 200, 200)
        pdf.line(lm, y, lm + W, y)
        pdf.ln(1)

    # Table column headers
    y = pdf.get_y()
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(lm, y, W, 6.5, style="F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(lm + 4, y + 0.8)
    pdf.cell(W - 50, 5.5, "Description")
    pdf.cell(46, 5.5, "Amount", align="R")
    pdf.ln(8)

    _fin_row("Gross Value of Work Executed to Date", gross_amount)
    _fin_row("Less: Previous Certificates Issued", previous_amount)
    _fin_divider()
    _fin_row("Value of Work This Certificate", current_amount, bold=True)
    _fin_row(f"Less: Retention ({retention_percentage:.1f}%)", retention_amount)
    _fin_divider()
    _fin_row("NET AMOUNT PAYABLE", net_amount, bold=True, highlight=True)

    if amount_paid > 0:
        pdf.ln(1)
        _fin_row("Amount Paid", amount_paid)
        _fin_row("Balance Outstanding", max(net_amount - amount_paid, 0.0))

    pdf.ln(4)

    # ─────────────────────────────────────────────────────────────────────────
    # WORK DESCRIPTION
    # ─────────────────────────────────────────────────────────────────────────
    if work_completed or description:
        _section_bar("SCOPE OF WORK")
        text = work_completed or description
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, text.strip(), border=0)
        pdf.ln(3)

    if notes:
        _section_bar("NOTES")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, notes.strip(), border=0)
        pdf.ln(3)

    # ─────────────────────────────────────────────────────────────────────────
    # APPROVAL & PAYMENT TIMELINE
    # ─────────────────────────────────────────────────────────────────────────
    _section_bar("CERTIFICATION & PAYMENT RECORD")

    def _timeline_row(event: str, dt: Optional[date], ref: str = "") -> None:
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(lm + 2, y)
        pdf.cell(55, 6, event + ":")
        pdf.set_font("Helvetica", "", 8)
        val = dt.strftime("%d %B %Y") if dt else "—"
        if ref:
            val += f"   Ref: {ref}"
        pdf.cell(0, 6, val)
        pdf.ln(6.5)

    _timeline_row("Certificate Issued", certificate_date)
    _timeline_row("Submitted for Approval", submitted_date)
    _timeline_row("Approved", approved_date)
    _timeline_row("Payment Made", payment_date, payment_reference)
    pdf.ln(4)

    # ─────────────────────────────────────────────────────────────────────────
    # SIGNATURE BLOCKS
    # ─────────────────────────────────────────────────────────────────────────
    _section_bar("AUTHORISATION")
    pdf.ln(2)

    sig_w = (W - 8) / 3
    sig_y = pdf.get_y()

    def _sig_block(title: str, name: str, x: float) -> None:
        pdf.set_draw_color(160, 160, 160)
        # Signature line
        pdf.line(x + 2, sig_y + 18, x + sig_w - 2, sig_y + 18)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(x + 2, sig_y + 19)
        pdf.cell(sig_w - 4, 5, title, border=0)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, sig_y + 24)
        pdf.cell(sig_w - 4, 4.5, name, border=0)
        # Date line
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, sig_y + 29)
        pdf.cell(18, 4.5, "Date:", border=0)
        pdf.line(x + 18, sig_y + 33, x + sig_w - 2, sig_y + 33)

    _sig_block("Prepared By", "Project Manager", lm)
    _sig_block("Certified By", consultant_name or "Consultant / QS", lm + sig_w + 4)
    _sig_block("Approved By", "Finance Director", lm + (sig_w + 4) * 2)

    pdf.set_y(sig_y + 38)
    pdf.ln(4)

    # ─────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_draw_color(_BR, _BG, _BB)
    pdf.set_line_width(0.5)
    pdf.line(lm, pdf.get_y(), lm + W, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.ln(2)
    pdf.set_x(lm)
    pdf.cell(W / 2, 4, "IMPERIAL HOMES LIMITED  •  CONFIDENTIAL", border=0)
    pdf.cell(W / 2, 4, f"Certificate: {certificate_number}  |  Generated: {date.today().strftime('%d %b %Y')}", border=0, align="R")

    return bytes(pdf.output())
