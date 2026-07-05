"""
Certificate PDF Generator
Generates an official-looking certificate PDF using ReportLab
whenever a Revenue Officer approves an application.
"""
import os
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_certificate_pdf(application, officer, cert_folder):
    """Generate a certificate PDF for an approved application.

    `application` and `officer` are expected to be sqlite3.Row objects (or
    dict-like), so fields are accessed with subscript notation, not
    attribute access.

    Returns the filename (not full path) of the generated PDF, which is
    saved inside `cert_folder`.
    """
    os.makedirs(cert_folder, exist_ok=True)
    filename = f"certificate_{application['application_no']}_{uuid.uuid4().hex[:6]}.pdf"
    filepath = os.path.join(cert_folder, filename)

    width, height = A4
    c = canvas.Canvas(filepath, pagesize=A4)

    # Outer decorative border
    c.setStrokeColor(colors.HexColor("#1a3c6e"))
    c.setLineWidth(3)
    c.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm)
    c.setLineWidth(0.75)
    c.rect(18 * mm, 18 * mm, width - 36 * mm, height - 36 * mm)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#1a3c6e"))
    c.drawCentredString(width / 2, height - 30 * mm, "GOVERNMENT OF INDIA")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 37 * mm, "REVENUE DEPARTMENT")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, height - 44 * mm, "Office of the Revenue Officer / Tahsildar")

    c.setStrokeColor(colors.HexColor("#1a3c6e"))
    c.line(40 * mm, height - 48 * mm, width - 40 * mm, height - 48 * mm)

    # Certificate title
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#a6192e"))
    c.drawCentredString(width / 2, height - 60 * mm, application["cert_type"].upper())

    # Certificate number and date
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(25 * mm, height - 72 * mm, f"Certificate No.: {application['application_no']}")
    c.drawRightString(width - 25 * mm, height - 72 * mm,
                       f"Date of Issue: {datetime.now().strftime('%d-%m-%Y')}")

    # Body text
    c.setFont("Helvetica", 11)
    body_y = height - 90 * mm
    line_height = 8 * mm

    cert_type = application["cert_type"]
    lines = [
        "This is to certify that the details furnished below have been verified",
        "and found to be true and correct as per the records available with",
        "this office, and the certificate is issued for official use.",
        "",
        f"Applicant Name       :  {application['applicant_name']}",
        f"Father's / Guardian's Name  :  {application['father_name'] or '-'}",
        f"Date of Birth        :  {application['dob'] or '-'}",
        f"Gender               :  {application['gender'] or '-'}",
        f"Caste / Community    :  {application['caste'] or '-'}",
        f"Religion             :  {application['religion'] or '-'}",
        f"Annual Income        :  Rs. {application['annual_income']}" if cert_type == "Income Certificate" and application["annual_income"] else None,
        f"Residential Address  :  {application['address'] or '-'}",
        f"Village / Town       :  {application['village'] or '-'}",
        f"Taluk                :  {application['taluk'] or '-'}",
        f"District             :  {application['district'] or '-'}",
        f"Purpose              :  {application['purpose'] or '-'}",
    ]
    lines = [l for l in lines if l is not None]

    for line in lines:
        c.drawString(25 * mm, body_y, line)
        body_y -= line_height

    # Footer / signature block
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, 40 * mm, "This is a system-generated certificate issued through the")
    c.drawString(25 * mm, 35 * mm, "Online Citizen Certificate Portal of the Revenue Department.")

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 25 * mm, 45 * mm, "Authorized Signatory")
    c.setFont("Helvetica", 10)
    officer_name = officer["full_name"] if officer else "Revenue Officer"
    c.drawRightString(width - 25 * mm, 40 * mm, officer_name)
    c.drawRightString(width - 25 * mm, 35 * mm, "Revenue Officer / Tahsildar")

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width / 2, 22 * mm,
                         "This certificate can be verified using the Certificate/Application Number on the portal.")

    c.showPage()
    c.save()

    return filename
