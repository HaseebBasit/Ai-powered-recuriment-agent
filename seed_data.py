import os
import shutil
import json
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, JobPost, Application, EmailLog, SystemConfig
from app.services.resume_parser import extract_resume_text

def seed():
    app = create_app()
    with app.app_context():
        print("Resetting and seeding database...")
        db.drop_all()
        db.create_all()

        # 1. Create Recruiter
        recruiter = User(
            email="recruiter@smarthire.ai",
            full_name="Sarah Jenkins",
            role="recruiter",
            phone="+1 (555) 234-5678",
            company="SmartHire Talent Solutions"
        )
        recruiter.set_password("password123")
        db.session.add(recruiter)

        # 2. Create Applicants
        applicant_ayesha = User(
            email="ayesha@example.com",
            full_name="Ayesha Khan",
            role="applicant",
            phone="+1 (555) 342-9182"
        )
        applicant_ayesha.set_password("password123")
        db.session.add(applicant_ayesha)

        applicant_bilal = User(
            email="bilal@example.com",
            full_name="Bilal Ahmed",
            role="applicant",
            phone="+1 (555) 782-4411"
        )
        applicant_bilal.set_password("password123")
        db.session.add(applicant_bilal)

        db.session.commit()

        # 3. Create Job Postings
        job_python = JobPost(
            recruiter_id=recruiter.id,
            title="Senior Python & AI Engineer",
            department="Engineering",
            location="Remote / Hybrid",
            employment_type="Full-time",
            min_experience=3,
            required_skills="Python, Flask, REST APIs, SQL, Docker, Git, Machine Learning",
            description=(
                "We are looking for an experienced Senior Python & AI Engineer to lead development of our "
                "intelligent recruitment and ATS screening platform. You will design high-throughput RESTful APIs "
                "using Flask/FastAPI, integrate Google Gemini and Groq AI models, and optimize SQL database architectures."
            ),
            status="Open",
            created_at=datetime.utcnow() - timedelta(days=5),
            deadline=datetime.utcnow() + timedelta(days=25)
        )
        db.session.add(job_python)

        job_fullstack = JobPost(
            recruiter_id=recruiter.id,
            title="Full Stack Web Developer",
            department="Product",
            location="New York, NY (Hybrid)",
            employment_type="Full-time",
            min_experience=2,
            required_skills="Python, Flask, JavaScript, React, HTML, CSS, SQL, Git",
            description=(
                "Join our frontend and backend team building modern web applications with Flask, Bootstrap, and React. "
                "You will collaborate closely with UI/UX designers to translate requirements into responsive, accessible web portals."
            ),
            status="Open",
            created_at=datetime.utcnow() - timedelta(days=3),
            deadline=datetime.utcnow() + timedelta(days=20)
        )
        db.session.add(job_fullstack)

        db.session.commit()

        # 4. Copy sample resumes to upload folder and create Applications
        samples_dir = os.path.join(os.path.dirname(__file__), "sample_resumes")
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads", "resumes")
        os.makedirs(uploads_dir, exist_ok=True)

        candidates = [
            {
                "name": "Ayesha Khan",
                "email": "ayesha@example.com",
                "phone": "+1 (555) 342-9182",
                "filename": "Ayesha_Khan_Resume.pdf",
                "user_id": applicant_ayesha.id,
                "score": 92,
                "status": "Shortlisted",
                "matching": ["Python", "Flask", "REST APIs", "SQL", "Docker", "Git", "Machine Learning"],
                "missing": [],
                "justification": "Exceptional match (92%). The candidate demonstrates extensive 5+ year background in Python, Flask microservices, SQL, and Docker, directly exceeding the 3-year requirement. Proven experience implementing AI/ATS features.",
                "questions": [
                    "1. Explain how you would design a REST API for job postings in Flask.",
                    "2. Describe a time you resolved a conflict in a team project.",
                    "3. How do you manage Docker container lifecycle and database migration in a continuous integration environment?",
                    "4. In your experience with PostgreSQL, what techniques do you use to diagnose and resolve slow queries?",
                    "5. Walk us through how you would architect a rate-limiting fallback strategy for high-concurrency LLM API requests."
                ]
            },
            {
                "name": "Bilal Ahmed",
                "email": "bilal@example.com",
                "phone": "+1 (555) 782-4411",
                "filename": "Bilal_Ahmed_Resume.docx",
                "user_id": applicant_bilal.id,
                "score": 78,
                "status": "Shortlisted",
                "matching": ["Python", "Flask", "REST APIs", "SQL", "Git"],
                "missing": ["Docker", "Machine Learning"],
                "justification": "Strong match (78%). Solid 3+ years experience with core Python, Flask, and relational database design. Highly capable on web architectures; would benefit from practical containerization exposure.",
                "questions": [
                    "1. How do you implement robust token-based user authentication and role management in Flask?",
                    "2. Describe how you structure a large Flask project using Blueprints and SQLAlchemy models.",
                    "3. What approaches do you take when designing responsive, accessible front-ends that communicate with RESTful APIs?",
                    "4. Tell us about a time you had to adapt quickly to changing technical requirements mid-sprint.",
                    "5. How do you write unit tests for Flask route endpoints and database operations?"
                ]
            },
            {
                "name": "Sara Malik",
                "email": "sara@example.com",
                "phone": "+1 (555) 912-3049",
                "filename": "Sara_Malik_Resume.pdf",
                "user_id": None,
                "score": 58,
                "status": "On Hold",
                "matching": ["Python", "SQL", "Git"],
                "missing": ["Flask", "Docker", "REST APIs", "Machine Learning"],
                "justification": "Moderate match (58%). Proficient in Python scripting and SQL data queries, but lacks documented production experience building web backends in Flask and containerizing applications with Docker.",
                "questions": [
                    "1. Walk us through how you would transition a Python data processing script into an event-driven REST API.",
                    "2. How do you optimize complex SQL joins and aggregate queries in relational databases?",
                    "3. Describe a challenging data inconsistency issue you encountered and how you solved it.",
                    "4. How do you collaborate with software engineers when handing off analytical models into production?",
                    "5. Describe a situation where you had to learn a completely new library under tight deadlines."
                ]
            },
            {
                "name": "Usman Raza",
                "email": "usman@example.com",
                "phone": "+1 (555) 601-8899",
                "filename": "Usman_Raza_Resume.docx",
                "user_id": None,
                "score": 31,
                "status": "Rejected",
                "matching": ["HTML", "CSS"],
                "missing": ["Python", "Flask", "SQL", "Docker", "REST APIs", "Machine Learning"],
                "justification": "Low match (31%). Candidate's background is primarily centered on UI/UX graphic design rather than backend software engineering and Python development.",
                "questions": [
                    "1. How do you translate design wireframes into clean, semantic HTML and CSS?",
                    "2. How do you communicate UI constraints with backend developers?",
                    "3. Describe a time you received constructive feedback on a design project and iterated on it.",
                    "4. What is your approach to conducting user research and usability testing?",
                    "5. What tools do you use to manage versioning and design handoffs in agile teams?"
                ]
            }
        ]

        for cand in candidates:
            src = os.path.join(samples_dir, cand["filename"])
            dst = os.path.join(uploads_dir, cand["filename"])
            if os.path.exists(src):
                shutil.copyfile(src, dst)

            extracted_txt = extract_resume_text(dst) if os.path.exists(dst) else f"Resume for {cand['name']}"

            app_record = Application(
                job_id=job_python.id,
                applicant_id=cand["user_id"],
                applicant_name=cand["name"],
                applicant_email=cand["email"],
                applicant_phone=cand["phone"],
                resume_filename=cand["filename"],
                resume_path=dst,
                extracted_text=extracted_txt,
                parsed_data=json.dumps({
                    "name": cand["name"],
                    "email": cand["email"],
                    "phone": cand["phone"],
                    "skills": cand["matching"] + ["Problem Solving"],
                    "experience_years": 4 if cand["score"] > 70 else 2,
                    "education": ["B.S. in Computer Science / IT"],
                    "projects": ["Web development and database management"]
                }),
                match_score=cand["score"],
                match_justification=cand["justification"],
                matching_skills=json.dumps(cand["matching"]),
                missing_skills=json.dumps(cand["missing"]),
                status=cand["status"],
                ai_feedback=(
                    f"SmartHire AI Career Guidance for {job_python.title}:\n"
                    f"1. Competency Alignment: Highlight tangible projects involving {', '.join(cand['missing'][:2]) if cand['missing'] else 'cloud infrastructure'}.\n"
                    f"2. Quantify Achievements: Include impact metrics (e.g. latency reduced by 30%, query speed improved).\n"
                    f"3. ATS Optimization: Ensure clean section headers for seamless automated parsing."
                ),
                interview_questions=json.dumps(cand["questions"]),
                applied_at=datetime.utcnow() - timedelta(hours=cand["score"] // 4)
            )
            db.session.add(app_record)

        # 5. Seed some initial email logs
        email_log1 = EmailLog(
            recipient="ayesha@example.com",
            subject="Application Received: Senior Python & AI Engineer at SmartHire",
            body="Hello Ayesha Khan,\n\nYour application for Senior Python & AI Engineer has been received and screened by SmartHire AI.\n\nSmartHire Team",
            status="Logged (No SMTP)",
            sent_at=datetime.utcnow() - timedelta(hours=2)
        )
        email_log2 = EmailLog(
            recipient="ayesha@example.com",
            subject="SmartHire Application Status Update: Senior Python & AI Engineer",
            body="Hello Ayesha Khan,\n\nCongratulations! You have been Shortlisted for the Senior Python & AI Engineer role.\n\nSmartHire Hiring Team",
            status="Logged (No SMTP)",
            sent_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.session.add(email_log1)
        db.session.add(email_log2)

        db.session.commit()
        print("Database successfully seeded with demo recruiters, jobs, and candidates matching the Brand Identity Guide!")

if __name__ == "__main__":
    seed()

