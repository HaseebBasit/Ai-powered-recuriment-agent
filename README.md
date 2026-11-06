# SmartHire: AI-Powered Resume Screening & Interview Preparation System

<p align="center">
  <img src="app/static/img/logo.png" alt="SmartHire Logo" width="300"/>
</p>

**SmartHire** is an intelligent, automated talent screening and interview preparation web platform designed for small companies, university placement offices, and student societies. It automates the first round of resume screening by extracting skills, education, and experience from PDF and Word DOCX resumes, comparing them with role requirements, and assigning an ATS match score (0–100%) with justifications, tailored interview questions, and candidate improvement advice.

---

## 🎨 Brand Identity & Visual Theme

Built with strict adherence to the **SmartHire Brand Identity Guide**:

- **Deep Indigo (`#3730A3` / `rgb(55, 48, 163)`)**: Primary brand color used for navigation, sidebars, primary action buttons, table headers, and links.
- **Teal (`#0D9488` / `rgb(13, 148, 136)`)**: Secondary / AI Accent color reserved for AI features (ATS match scores, tailored interview question cards, resume feedback, and AI badges).
- **Amber (`#F59E0B` / `rgb(245, 158, 11)`)**: Highlight / CTA color used for high-visibility actions like *Apply Now* and score highlights.
- **Functional Status Colors**:
  - **Shortlisted / High Match (70–100%)**: Green (`#16A34A`)
  - **On Hold / Medium Match (40–69%)**: Amber (`#F59E0B`)
  - **Rejected / Low Match (0–39%)**: Red (`#DC2626`)
  - **Applied / New**: Sky Blue (`#0EA5E9`)
- **Neutrals**:
  - Page Background: `#F8FAFC`
  - Cards & Clean Surfaces: `#FFFFFF`
  - Subtle Borders: `#E2E8F0`
  - Body Text: `#1E293B`
  - Muted Text: `#64748B`

---

## 🚀 Key Functional Features

1. **Role-Based Authentication & Access Control**
   - Secure authentication for two distinct roles: **Recruiter** and **Applicant**.
   - Password hashing via Werkzeug with session persistence via Flask-Login.

2. **Job Postings Management (Recruiter)**
   - Create, edit, toggle (Open/Closed), and delete job postings.
   - Specify job title, department, location, employment type, minimum experience, required skills, and descriptions.

3. **Resume Ingestion & Multi-Format Parsing**
   - Accepts both **PDF (`.pdf`)** and **Microsoft Word (`.docx`)** files up to 10MB.
   - Text extracted using **PyMuPDF (`fitz`)** and **`python-docx`**.

4. **Multi-Tier AI Screening & Resilient Fallback Engine**
   - **Primary AI**: Google Gemini API free tier (`google-genai`).
   - **Secondary Fallback**: Groq Cloud API free tier (`groq`).
   - **Heuristic NLP Fallback**: Built-in deterministic NLP taxonomy parser that ensures zero crashes even during API rate limits or network offline scenarios.
   - Calculates ATS match score (0–100%), extracts candidate skills, and identifies skill gaps.

5. **Ranked Applicant List & Recruiter Workflow**
   - Ranked candidate tables sorted by match score descending.
   - Visual score progress bars in exact brand colors.
   - Live filters by keyword, match score range (High/Medium/Low), and application status.
   - Single-click recruiter actions: **Shortlist**, **Put On Hold**, **Reject**, with internal recruiter notes.

6. **Tailored AI Interview Questions**
   - Generates 5 custom interview questions (3 Technical + 2 Behavioral) based on candidate's actual resume against the role requirements.
   - Regenerate questions dynamically from the recruiter applicant view.

7. **AI Resume Feedback for Applicants**
   - Dedicated feedback dashboard giving applicants actionable advice to improve their resume for the targeted role (quantifiable metrics, missing keywords, ATS formatting).

8. **Automated Email Communications (Gmail SMTP)**
   - Automatic email triggers:
     - Application Received confirmation (to applicant)
     - Application Shortlisted notice (to applicant)
     - Application Status update / Rejection notice (to applicant)
     - Daily Recruiter Digest summarizing new applications and average scores
   - Fallback logging: Automatically records all communications to the `EmailLog` database table if SMTP credentials are not active.

9. **Automated Scheduled Jobs (APScheduler)**
   - Daily cron job runs in the background to aggregate application stats and dispatch daily email digests to recruiters.
   - Instant "Trigger Daily Digest Now" button for testing.

10. **Export Reports**
    - One-click export of ranked candidate lists as **CSV** or styled **PDF** reports (generated via ReportLab with brand colors and tables).

11. **Recruiter Analytics Dashboard**
    - High-level KPIs: Active jobs, total applicants, average ATS match score, and shortlisted counts.
    - Interactive **Chart.js** charts for applications per job and status distribution donuts.
    - Frequency cloud of most common candidate skills.

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Bootstrap Icons, Chart.js, Custom Brand Theme
- **AI APIs**: Google Gemini API (`google-genai`), Groq Cloud API (`groq`)
- **Document Parsing**: PyMuPDF (`fitz`), python-docx
- **Automation & Scheduler**: APScheduler, Python `smtplib` (Gmail SMTP)
- **PDF & CSV Generation**: ReportLab, Python standard `csv` and `io`

---

## 📋 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Activate Virtual Environment
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your API keys (optional; intelligent heuristic fallback works out of the box):
```ini
SECRET_KEY=smarthire_secret_key_hackathon_2026_dev
DATABASE_URL=sqlite:///../data/smarthire.db

# Free Tier AI APIs (Optional)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Gmail SMTP Email (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_char_app_password
```

### 5. Seed Demo Data
Pre-populate the database with recruiters, jobs, and sample applicants matching the brand guide:
```bash
python seed_data.py
```

### 6. Run the Application
```bash
python run.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🔑 Demo Login Credentials

For quick evaluation during demos and testing:

| Role | Email | Password | Features |
|---|---|---|---|
| **Recruiter** | `recruiter@smarthire.ai` | `password123` | Dashboard, Ranked Applicants, PDF/CSV Export, Status Updates, AI Questions, Settings |
| **Applicant** | `ayesha@example.com` | `password123` | Application History, ATS Score (92%), AI Resume Improvement Feedback |
| **Applicant** | `bilal@example.com` | `password123` | Application History, ATS Score (78%), AI Resume Feedback |

You can also click the quick-login buttons on the Sign In page to auto-fill credentials!

---

## 🧪 Running Automated Tests

Run the test suite verifying routes, database models, AI fallback logic, and resume file upload screening:
```bash
python test_app.py
```

