"""Handover Certificate PDF generator — Imperial Homes branded A4 document (SOP 5.0)."""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"
_BR, _BG, _BB = 180, 37, 65
_LR, _LG, _LB = 250, 242, 244
_GR, _GG, _GB = 245, 245, 245


def _tick(done: bool) -> str:
    return "✓" if done else "✗"


def generate_handover_certificate_pdf(
    *,
    handover_id: str,
    status: str,
    # Property
    property_name: str,
    apartment_number: str = "",
    site_location: str = "",
    # Client
    client_name: str,
    client_email: str = "",
    client_phone: str = "",
    # Financial obligations
    sinking_fund_invoiced: bool = False,
    sinking_fund_amount: Optional[float] = None,
    transfer_document_invoiced: bool = False,
    transfer_document_amount: Optional[float] = None,
    hoa_forms_completed: bool = False,
    facility_manager_info_provided: bool = False,
    all_payments_made: bool = False,
    payments_date: Optional[datetime] = None,
    # Pack / approval
    handover_pack_drafted: bool = False,
    doa_approved: bool = False,
    doa_approved_date: Optional[datetime] = None,
    # Sign-off
    client_signed: bool = False,
    client_signed_date: Optional[datetime] = None,
    keys_handed_over: bool = False,
    handover_date: Optional[datetime] = None,
    # Narrative
    letter_to_client: str = "",
    notes: str = "",
    issues_noted: str = "",
    # Handler
    handled_by: str = "",
    currency: str = "GHS",
) -> bytes:
    """Return a Handover Certificate PDF as raw bytes."""
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
    pdf.cell(W, 7, "PROPERTY HANDOVER CERTIFICATE", align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(44)

    # ── Reference band ────────────────────────────────────────────────────────
    ref_y = pdf.get_y() + 2
    pdf.set_fill_color(_LR, _LG, _LB)
    pdf.rect(lm, ref_y, W, 9, style="F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(_BR, _BG, _BB)
    pdf.set_xy(lm + 2, ref_y + 1.5)
    pdf.cell(40, 6, f"Handover ID:  {handover_id}")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(55, 6, f"Property: {property_name[:30]}")
    if handover_date:
        pdf.cell(55, 6, f"Handover Date: {handover_date.strftime('%d %b %Y')}")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(_BR, _BG, _BB)
    pdf.cell(0, 6, status.replace("_", " ").upper())
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(ref_y + 13)

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
        pdf.cell(38, 5.5, l1 + ":")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(col - 42, 5.5, v1)
        if l2:
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(38, 5.5, l2 + ":")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5.5, v2)
        pdf.ln(7)

    # ── Property details ──────────────────────────────────────────────────────
    _sbar("PROPERTY DETAILS")
    _irow("Property Name", property_name, "Unit/Apartment", apartment_number or "—")
    if site_location:
        _irow("Site Location", site_location)
    pdf.ln(2)

    # ── Client details ────────────────────────────────────────────────────────
    _sbar("CLIENT / PURCHASER DETAILS")
    _irow("Client Name", client_name)
    _irow("Email", client_email or "—", "Phone", client_phone or "—")
    pdf.ln(2)

    # ── Obligations checklist ─────────────────────────────────────────────────
    _sbar("HANDOVER OBLIGATIONS CHECKLIST  (SOP 5.0)")
    pdf.ln(1)

    checklist = [
        (sinking_fund_invoiced, "Sinking Fund Invoiced",
         f"{currency} {sinking_fund_amount:,.2f}" if sinking_fund_amount else ""),
        (transfer_document_invoiced, "Transfer Document Invoiced",
         f"{currency} {transfer_document_amount:,.2f}" if transfer_document_amount else ""),
        (hoa_forms_completed, "HOA Forms Completed", ""),
        (facility_manager_info_provided, "Facility Manager Information Provided", ""),
        (all_payments_made, "All Payments Made / Cleared",
         payments_date.strftime("%d %b %Y") if payments_date else ""),
        (handover_pack_drafted, "Handover Pack Drafted", ""),
        (doa_approved, "DOA / Management Approval",
         doa_approved_date.strftime("%d %b %Y") if doa_approved_date else ""),
        (client_signed, "Client Sign-off Received",
         client_signed_date.strftime("%d %b %Y") if client_signed_date else ""),
        (keys_handed_over, "Keys Handed Over", ""),
    ]

    for done, label, note in checklist:
        y = pdf.get_y()
        # Tick box
        tick_r, tick_g, tick_b = (34, 139, 34) if done else (200, 50, 50)
        pdf.set_fill_color(tick_r, tick_g, tick_b)
        pdf.rect(lm + 2, y + 1, 6, 5, style="F")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(lm + 2, y + 0.8)
        pdf.cell(6, 5, "✓" if done else "✗", align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B" if done else "", 8.5)
        pdf.set_xy(lm + 11, y + 0.8)
        pdf.cell(100, 5, label)
        if note:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, note)
            pdf.set_text_color(0, 0, 0)
        pdf.ln(7)

    # Completion status pill
    pdf.ln(2)
    all_done = all(item[0] for item in checklist)
    pill_r, pill_g, pill_b = (34, 139, 34) if all_done else (_BR, _BG, _BB)
    y = pdf.get_y()
    pdf.set_fill_color(pill_r, pill_g, pill_b)
    pdf.rect(lm, y, W, 8, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(lm, y + 1)
    label_text = "ALL OBLIGATIONS COMPLETE — HANDOVER FINALISED" if all_done else f"STATUS: {status.replace('_', ' ').upper()}"
    pdf.cell(W, 6, label_text, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(12)

    # ── Communication / letter to client ─────────────────────────────────────
    if letter_to_client:
        _sbar("STEPS COMMUNICATED TO CLIENT")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, letter_to_client.strip())
        pdf.ln(2)

    if issues_noted:
        _sbar("ISSUES / SNAGS NOTED AT HANDOVER")
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, issues_noted.strip())
        pdf.ln(2)

    if notes:
        _sbar("ADDITIONAL NOTES")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_x(lm + 2)
        pdf.multi_cell(W - 4, 5.5, notes.strip())
        pdf.ln(2)

    # ── Signature blocks ──────────────────────────────────────────────────────
    _sbar("ACKNOWLEDGEMENT & SIGN-OFF")
    pdf.ln(4)
    sig_w = (W - 8) / 3
    sig_y = pdf.get_y()

    for i, (role, name) in enumerate([
        ("Client / Purchaser", client_name),
        ("Handled By / Sales", handled_by or "Sales Officer"),
        ("Management Approval", "Director / DOA"),
    ]):
        x = lm + i * (sig_w + 4)
        pdf.set_draw_color(160, 160, 160)
        pdf.line(x + 2, sig_y + 18, x + sig_w - 2, sig_y + 18)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(x + 2, sig_y + 19)
        pdf.cell(sig_w - 4, 5, role)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, sig_y + 24)
        pdf.cell(sig_w - 4, 5, name)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, sig_y + 30)
        pdf.cell(12, 4, "Date:")
        pdf.line(x + 14, sig_y + 34, x + sig_w - 2, sig_y + 34)

    pdf.set_y(sig_y + 38)

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
    pdf.cell(W / 2, 4, "IMPERIAL HOMES LIMITED  •  PROPERTY HANDOVER  •  SOP 5.0")
    pdf.cell(W / 2, 4, f"Ref: {handover_id}  |  Generated: {date.today().strftime('%d %b %Y')}", align="R")

    return bytes(pdf.output())
