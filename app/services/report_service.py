import io
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pathlib import Path

def generate_applicants_csv(job, applications):
    """Generate a CSV report of ranked applicants for a job"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Rank", "Applicant Name", "Email", "Phone",
        "Match Score (%)", "Status", "Matching Skills",
        "Missing Skills", "Applied Date", "Recruiter Notes"
    ])
    
    # Rows (assumed already sorted by match_score desc)
    for idx, app in enumerate(applications, start=1):
        matching = ", ".join(app.get_matching_skills_list())
        missing = ", ".join(app.get_missing_skills_list())
        writer.writerow([
            idx,
            app.applicant_name,
            app.applicant_email,
            app.applicant_phone or "",
            f"{app.match_score}%",
            app.status,
            matching,
            missing,
            app.applied_at.strftime("%Y-%m-%d %H:%M"),
            app.recruiter_notes or ""
        ])
        
    output.seek(0)
    return output.getvalue()

def generate_applicants_pdf(job, applications):
    """Generate a branded PDF report using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    PRIMARY = colors.HexColor("#3730A3")      # Deep Indigo
    TEAL = colors.HexColor("#0D9488")         # Teal
    AMBER = colors.HexColor("#F59E0B")        # Amber
    GREEN = colors.HexColor("#16A34A")        # Green
    RED = colors.HexColor("#DC2626")          # Red
    DARK_SLATE = colors.HexColor("#1E293B")   # Slate
    MUTED = colors.HexColor("#64748B")        # Muted
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Background
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=MUTED,
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.white,
        alignment=1  # Centered
    )
    
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_SLATE,
        leading=12
    )
    
    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=DARK_SLATE,
        leading=12
    )

    story = []
    
    # Header Banner / Logo
    logo_path = Path(__file__).resolve().parent.parent / "static" / "img" / "logo.png"
    if logo_path.exists():
        try:
            # Add logo
            img = RLImage(str(logo_path), width=2.2*inch, height=0.6*inch)
            img.hAlign = 'LEFT'
            story.append(img)
            story.append(Spacer(1, 10))
        except Exception:
            pass
            
    story.append(Paragraph(f"AI-Powered Recruitment Agent &mdash; Candidate Ranking Report", title_style))
    story.append(Paragraph(
        f"<b>Job Title:</b> {job.title} &nbsp;|&nbsp; <b>Department:</b> {job.department} &nbsp;|&nbsp; "
        f"<b>Required Experience:</b> {job.min_experience}+ Years &nbsp;|&nbsp; <b>Date:</b> {datetime.utcnow().strftime('%B %d, %Y')}",
        subtitle_style
    ))
    
    # Summary Info Card
    total_cand = len(applications)
    shortlisted = sum(1 for a in applications if a.match_score >= 70 or a.status == "Shortlisted")
    on_hold = sum(1 for a in applications if 40 <= a.match_score < 70 or a.status == "On Hold")
    rejected = sum(1 for a in applications if a.match_score < 40 or a.status == "Rejected")
    avg_score = round(sum(a.match_score for a in applications) / total_cand) if total_cand else 0
    
    summary_data = [
        [
            Paragraph(f"<b>Total Applicants:</b> {total_cand}", cell_style),
            Paragraph(f"<b>Avg Match Score:</b> <font color='#0D9488'><b>{avg_score}%</b></font>", cell_style),
            Paragraph(f"<b>Shortlisted:</b> <font color='#16A34A'><b>{shortlisted}</b></font>", cell_style),
            Paragraph(f"<b>On Hold:</b> <font color='#F59E0B'><b>{on_hold}</b></font>", cell_style),
            Paragraph(f"<b>Rejected:</b> <font color='#DC2626'><b>{rejected}</b></font>", cell_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[110, 110, 100, 100, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Table Data
    table_data = [
        [
            Paragraph("Rank", header_style),
            Paragraph("Applicant Name", header_style),
            Paragraph("Match Score", header_style),
            Paragraph("Status", header_style),
            Paragraph("Matching Skills", header_style),
            Paragraph("Applied Date", header_style)
        ]
    ]
    
    for idx, app in enumerate(applications, start=1):
        matching = ", ".join(app.get_matching_skills_list()[:4])
        if not matching:
            matching = "Evaluated via ATS"
            
        # Status Color Tagging
        if app.match_score >= 70 or app.status == "Shortlisted":
            sc_color = "#16A34A"
        elif app.match_score >= 40 or app.status == "On Hold":
            sc_color = "#F59E0B"
        else:
            sc_color = "#DC2626"
            
        score_para = Paragraph(f"<font color='{sc_color}'><b>{app.match_score}%</b></font>", cell_bold)
        status_para = Paragraph(f"<font color='{sc_color}'><b>{app.status}</b></font>", cell_bold)
        
        table_data.append([
            Paragraph(f"#{idx}", cell_bold),
            Paragraph(f"<b>{app.applicant_name}</b><br/><font color='#64748B'>{app.applicant_email}</font>", cell_style),
            score_para,
            status_para,
            Paragraph(matching, cell_style),
            Paragraph(app.applied_at.strftime("%b %d, %Y"), cell_style)
        ])
        
    col_widths = [45, 145, 75, 75, 130, 70]
    cand_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    cand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    
    story.append(cand_table)
    
    # Footer Note
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<font size='8' color='#94A3B8'>Report generated automatically by AI-Powered Recruitment Agent &bull; Intelligent Resume Screening &amp; Ranking System.</font>",
        subtitle_style
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

