# AI Powered Recruitment Agent

<p align="center">
  <img src="app/static/img/logo.png" alt="AI Powered Recruitment Agent logo" width="300"/>
</p>

**AI Powered Recruitment Agent** is a web application that automates the first round of resume screening. A recruiter posts a job, applicants upload a resume (PDF or DOCX), and an AI agent extracts skills, education and experience, compares them with the job requirements, and returns a 0–100 match score with a short justification, the matching and missing skills, tailored interview questions, and resume improvement advice. Recruiters review a ranked list and make the final decision.

Built for the **Vultr: Agent Rush Hackathon** (Challenge 2: Powering the Future of Work, HR & Recruitment).

---

## Deployment Status

This project is designed to run on a **Vultr Cloud Compute VM** (see [Vultr Architecture](#vultr-architecture-and-deployment-plan)).

The Vultr hackathon credit pool was exhausted before we could verify a Vultr account and deploy, so **there is no live Vultr deployment yet**. The organizers advised us to submit with the repository, demo video and slides. We are in contact with the Vultr team about credits and will update this section once the app is deployed.

You can run the full application locally in a few minutes (see [Quick Start](#quick-start)).

---

## The Problem

Small companies, university placement offices and student societies often receive hundreds of resumes for a single role. Screening them by hand is slow and inconsistent, and small teams cannot afford recruiting software.

## How the Agent Works

When an applicant applies to a job, the agent runs a multi-step workflow and stores real results in the database:

1. **Extract:** text is pulled from the uploaded PDF or DOCX (PyMuPDF, python-docx).
2. **Parse:** an LLM converts the text into structured fields: name, contact, skills, education, experience, projects.
3. **Score:** the resume is compared with the job. The result is a 0–100 match score, a short justification, matching skills and missing skills.
4. **Rank:** applicants for each job are ranked by score and can be filtered by score range, keyword and status.
5. **Decide:** the recruiter shortlists, holds or rejects each candidate. The AI never makes the final decision.
6. **Prepare:** tailored interview questions (3 technical, 2 behavioral) are generated for a candidate from their actual resume and the role.
7. **Communicate:** status emails go to applicants, and a daily digest goes to recruiters.

---

## Features

**Accounts and roles**
- Register, log in and log out securely, with two roles: Recruiter and Applicant.
- Password hashing with Werkzeug and session handling with Flask-Login.

**Recruiter tools**
- Create, edit, open/close and delete job postings (title, department, location, employment type, minimum experience, required skills, description).
- Ranked applicant list with score bars and filters by keyword, score range (High/Medium/Low) and status.
- One-click Shortlist, Put On Hold and Reject, with internal notes.
- AI-generated interview questions per candidate, with a regenerate option.
- Analytics dashboard: active jobs, total applicants, average match score, shortlisted count, applications per job (Chart.js), status distribution and most common candidate skills.
- Export the ranked applicant list as CSV or PDF (ReportLab).

**Applicant tools**
- Browse and search open jobs, then apply with a PDF or DOCX resume (maximum 10 MB).
- Match score with strengths and missing skills for each application.
- AI resume feedback with actionable suggestions for the targeted role.

**Standalone AI Tools page**
- Live resume screening against any role and skill list.
- Interview question generator from a role, skills and job description.
- Resume feedback with an estimated match score.

**Automation and reliability**
- Automated emails through Gmail SMTP: application received, shortlisted, rejected, and a daily recruiter digest.
- APScheduler runs the daily digest job. A "Trigger Daily Digest Now" button is available for testing.
- File type and size validation on every upload.
- Multi-tier AI engine: Google Gemini first, Groq as a fallback, and a built-in rule-based skill matcher if both APIs are unavailable. If SMTP is not configured, emails are recorded in an `EmailLog` table instead.

---

## Technology Stack

| Area | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug |
| Database | SQLite (SQLAlchemy ORM) |
| Frontend | HTML5, CSS3, Bootstrap 5, Bootstrap Icons, Chart.js, JavaScript |
| AI | Google Gemini API (`google-genai`), Groq API (`groq`) |
| Resume parsing | PyMuPDF (`fitz`), python-docx |
| Automation | APScheduler, Python `smtplib` (Gmail SMTP) |
| Reports | ReportLab, Python `csv` |
| Tools | Antigravity, VS Code, Git, GitHub |
| Planned hosting | Vultr Cloud Compute |

---

## Vultr Architecture and Deployment Plan

Vultr is intended to be the central backend for the application, not static hosting.

```
Browser
   |  HTTPS
   v
Nginx or Caddy (reverse proxy, TLS)        <- Vultr Cloud Compute VM (Ubuntu)
   |
   v
Gunicorn running the Flask app
   |-- SQLite database (data/)
   |-- Uploaded resumes (uploads/resumes/)
   |-- APScheduler (daily recruiter digest)
   |-- Gemini API  ->  Groq API (fallback)  ->  rule-based matcher
   `-- Gmail SMTP (status emails)
```

What the Vultr VM is meant to host: the web app, the database, resume storage, the scheduler, and all workflow orchestration. API keys are kept in environment variables on the server, never in the repository.

### Planned deployment steps (Ubuntu VM)

```bash
# 1. On a fresh Vultr Ubuntu VM
sudo apt update && sudo apt install -y python3-venv python3-pip nginx git

# 2. Get the code
git clone <this-repository-url> app && cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt gunicorn

# 3. Configure environment
cp .env.example .env     # then edit .env with real keys

# 4. Seed demo data (optional)
python seed_data.py

# 5. Run with ONE worker (so the scheduler does not send duplicate digests)
gunicorn -w 1 -b 127.0.0.1:8000 "run:app"
```

Then configure Nginx (or Caddy) to proxy port 80/443 to `127.0.0.1:8000` and run gunicorn as a systemd service. The exact `run:app` entry point depends on how `run.py` exposes the Flask application.

> This section describes the intended deployment. It has not been run on Vultr yet (see Deployment Status).

---

## Quick Start

### 1. Prerequisites
Python 3.10 or newer.

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your values. The AI and email keys are optional: without them the app uses the rule-based matcher and logs emails to the database.

```ini
SECRET_KEY=change_me_to_a_long_random_string
DATABASE_URL=sqlite:///../data/smarthire.db

# Free-tier AI APIs (optional)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Gmail SMTP (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_char_app_password
```

Never commit your `.env` file.

### 5. Seed demo data
Creates sample recruiters, jobs and applicants:
```bash
python seed_data.py
```

### 6. Run the application
```bash
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## Demo Login Credentials

These accounts are created by `seed_data.py` for local demos only. Change or remove them before any real deployment.

| Role | Email | Password |
|---|---|---|
| Recruiter | `recruiter@smarthire.ai` | `password123` |
| Applicant | `ayesha@example.com` | `password123` |
| Applicant | `bilal@example.com` | `password123` |

The Sign In page also has quick-login buttons that fill these credentials.

Sample resumes for testing can be generated with:
```bash
python generate_sample_resumes.py
```
Use sample or fictional resumes for demos, not real people's data.

---

## Containment and Safety

- Uploads are validated for file type (PDF, DOCX) and size (10 MB maximum).
- Resume files are only parsed as text; they are never executed.
- API keys and mail credentials live in environment variables, not in code.
- The AI scores, explains and drafts; recruiters make every final decision.
- API errors trigger a fallback from Gemini to Groq, then to a rule-based matcher.

---

## Project Structure

```
app/              Flask application (routes, models, templates, static files)
data/             SQLite database (not committed)
uploads/resumes/  Uploaded resumes (not committed)
sample_resumes/   Sample resumes for testing
run.py            Application entry point
seed_data.py      Demo data loader
test_app.py       Automated tests
```

---

## Running Tests

```bash
python test_app.py
```

---

## Brand Palette

| Use | Color |
|---|---|
| Primary (navigation, buttons, links) | Deep Indigo `#3730A3` |
| AI features (scores, questions, feedback) | Teal `#0D9488` |
| Highlights and calls to action | Amber `#F59E0B` |
| Shortlisted / high match (70–100) | Green `#16A34A` |
| On hold / medium match (40–69) | Amber `#F59E0B` |
| Rejected / low match (0–39) | Red `#DC2626` |
| Applied / new | Sky Blue `#0EA5E9` |
| Background / surfaces / borders | `#F8FAFC` / `#FFFFFF` / `#E2E8F0` |
| Body text / muted text | `#1E293B` / `#64748B` |

---

## License

MIT. See the `LICENSE` file.
