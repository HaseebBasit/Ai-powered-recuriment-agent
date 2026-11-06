import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import docx

SAMPLES_DIR = Path(__file__).resolve().parent / "sample_resumes"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads" / "resumes"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def create_pdf_resume(filepath, name, email, phone, title, summary, skills, experience, education, projects):
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#3730A3'), spaceAfter=2)
    contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#64748B'), spaceAfter=10)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0D9488'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#1E293B'), leading=13)
    
    story = [
        Paragraph(name, title_style),
        Paragraph(f"{email} | {phone} | {title}", contact_style),
        Spacer(1, 4),
        Paragraph("Professional Summary", section_style),
        Paragraph(summary, body_style),
        Spacer(1, 4),
        Paragraph("Technical Skills", section_style),
        Paragraph(", ".join(skills), body_style),
        Spacer(1, 4),
        Paragraph("Work Experience", section_style)
    ]
    
    for exp in experience:
        story.append(Paragraph(f"<b>{exp['role']}</b> - {exp['company']} ({exp['period']})", body_style))
        story.append(Paragraph(exp['details'], body_style))
        story.append(Spacer(1, 3))
        
    story.append(Paragraph("Education", section_style))
    for edu in education:
        story.append(Paragraph(f"<b>{edu['degree']}</b> - {edu['school']} ({edu['year']})", body_style))
        
    story.append(Paragraph("Key Projects", section_style))
    for proj in projects:
        story.append(Paragraph(f"<b>{proj['name']}</b>: {proj['desc']}", body_style))
        story.append(Spacer(1, 2))
        
    doc.build(story)

def create_docx_resume(filepath, name, email, phone, title, summary, skills, experience, education, projects):
    doc = docx.Document()
    
    # Header
    h1 = doc.add_heading(name, level=0)
    p_contact = doc.add_paragraph(f"{email} | {phone} | {title}")
    p_contact.runs[0].font.color.rgb = docx.shared.RGBColor(100, 116, 139)
    
    # Summary
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(summary)
    
    # Skills
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph(", ".join(skills))
    
    # Experience
    doc.add_heading("Work Experience", level=1)
    for exp in experience:
        p = doc.add_paragraph()
        p.add_run(f"{exp['role']} - {exp['company']} ({exp['period']})\n").bold = True
        p.add_run(exp['details'])
        
    # Education
    doc.add_heading("Education", level=1)
    for edu in education:
        p = doc.add_paragraph()
        p.add_run(f"{edu['degree']} - {edu['school']} ({edu['year']})").bold = True
        
    # Projects
    doc.add_heading("Key Projects", level=1)
    for proj in projects:
        p = doc.add_paragraph()
        p.add_run(f"{proj['name']}: ").bold = True
        p.add_run(proj['desc'])
        
    doc.save(str(filepath))

def main():
    print("Generating sample resumes...")
    
    # 1. Ayesha Khan (High Match Python/Flask/AI - 92%)
    ayesha_pdf = SAMPLES_DIR / "Ayesha_Khan_Resume.pdf"
    create_pdf_resume(
        filepath=ayesha_pdf,
        name="Ayesha Khan",
        email="ayesha@example.com",
        phone="+1 (555) 342-9182",
        title="Senior Python & Backend Engineer",
        summary="Senior Software Engineer with 5+ years of hands-on experience designing scalable microservices in Python, Flask, and PostgreSQL. Proven track record deploying AI integrations, Docker containers, and optimizing REST APIs.",
        skills=["Python", "Flask", "FastAPI", "SQL", "PostgreSQL", "Docker", "REST APIs", "Git", "Redis", "Machine Learning", "CI/CD"],
        experience=[
            {
                "role": "Senior Backend Developer",
                "company": "Apex Software Labs",
                "period": "2022 - Present",
                "details": "Architected Flask and FastAPI microservices serving over 2M API queries monthly. Automated deployment pipelines with Docker and GitHub Actions, cutting deploy time by 40%."
            },
            {
                "role": "Python Software Engineer",
                "company": "DataStream Solutions",
                "period": "2019 - 2022",
                "details": "Engineered RESTful endpoints and optimized complex SQL queries in PostgreSQL, improving database throughput by 35%."
            }
        ],
        education=[
            {"degree": "B.S. in Computer Science", "school": "National University of Sciences & Technology", "year": "2019"}
        ],
        projects=[
            {"name": "AI ATS Screening Platform", "desc": "Built an intelligent document processing engine using Python, PyMuPDF, and vector matching algorithms."},
            {"name": "Distributed Job Scheduler", "desc": "Implemented asynchronous background job processing using Celery and Redis."}
        ]
    )
    
    # 2. Bilal Ahmed (High Match Web Developer - 78%)
    bilal_docx = SAMPLES_DIR / "Bilal_Ahmed_Resume.docx"
    create_docx_resume(
        filepath=bilal_docx,
        name="Bilal Ahmed",
        email="bilal@example.com",
        phone="+1 (555) 782-4411",
        title="Full Stack Software Developer",
        summary="Full Stack Developer with 3+ years experience building web applications using Python, Flask, JavaScript, React, and SQL. Passionate about clean code, robust RESTful APIs, and user-centric interfaces.",
        skills=["Python", "Flask", "JavaScript", "React", "HTML", "CSS", "Bootstrap", "SQL", "Git", "REST APIs"],
        experience=[
            {
                "role": "Full Stack Developer",
                "company": "Nexus Technologies",
                "period": "2021 - Present",
                "details": "Built and maintained Flask backends integrated with React frontends for corporate management portals. Designed relational schemas in SQLite and MySQL."
            }
        ],
        education=[
            {"degree": "B.S. in Software Engineering", "school": "COMSATS University", "year": "2021"}
        ],
        projects=[
            {"name": "E-Commerce REST API", "desc": "Developed a complete e-commerce backend in Flask with JWT authentication and Stripe webhook integration."},
            {"name": "Resume Builder UI", "desc": "Created a responsive web app using Bootstrap 5 and modern JavaScript."}
        ]
    )

    # 3. Sara Malik (Medium Match - 58% - On Hold)
    sara_pdf = SAMPLES_DIR / "Sara_Malik_Resume.pdf"
    create_pdf_resume(
        filepath=sara_pdf,
        name="Sara Malik",
        email="sara@example.com",
        phone="+1 (555) 912-3049",
        title="Junior Data Analyst & Python Programmer",
        summary="Data Analyst with 1.5 years experience in Python data analysis, Pandas, SQL, and data visualization. Familiar with Python scripting and basic Flask development.",
        skills=["Python", "SQL", "Pandas", "NumPy", "Data Analysis", "Git", "HTML"],
        experience=[
            {
                "role": "Junior Data Analyst",
                "company": "Insight Analytics Corp",
                "period": "2023 - Present",
                "details": "Extracted insights from relational databases using SQL queries and automated reporting with Python scripts."
            }
        ],
        education=[
            {"degree": "B.S. in Information Technology", "school": "Punjab University", "year": "2023"}
        ],
        projects=[
            {"name": "Customer Churn Prediction", "desc": "Analyzed customer datasets with Pandas and built scikit-learn models."}
        ]
    )

    # 4. Usman Raza (Low Match - 31% - Rejected)
    usman_docx = SAMPLES_DIR / "Usman_Raza_Resume.docx"
    create_docx_resume(
        filepath=usman_docx,
        name="Usman Raza",
        email="usman@example.com",
        phone="+1 (555) 601-8899",
        title="Junior Graphic & UI/UX Designer",
        summary="Creative designer with 1 year experience focusing on Figma, Adobe Photoshop, and front-end HTML/CSS styling. Basic knowledge of computer systems.",
        skills=["Figma", "HTML", "CSS", "Photoshop", "Illustrator"],
        experience=[
            {
                "role": "Design Intern",
                "company": "Creative Wave Agency",
                "period": "2024",
                "details": "Designed wireframes, UI mockups, and marketing collaterals for client websites."
            }
        ],
        education=[
            {"degree": "Diploma in Multimedia & Graphic Design", "school": "Polytechnic Institute", "year": "2024"}
        ],
        projects=[
            {"name": "Brand Design System", "desc": "Created typography guides and color palettes for web applications."}
        ]
    )

    print("Sample resumes generated in 'sample_resumes/'.")

if __name__ == "__main__":
    main()

