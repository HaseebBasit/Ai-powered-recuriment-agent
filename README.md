# AI Powered Recruitment Agent

<p align="center">
  <img src="app/static/img/logo.png" alt="AI Powered Recruitment Agent logo" width="300"/>
</p>

**AI Powered Recruitment Agent** is a web application that automates the first round of hiring. Recruiters post jobs, applicants upload resumes (PDF or DOCX), and an AI agent scores each resume against the job, explains the score, lists matching and missing skills, prepares interview questions and gives resume feedback. Recruiters review a ranked list and make every final decision.

It is built for small companies, university placement offices and student societies. Built for the **Vultr: Agent Rush Hackathon** (Challenge 2: Powering the Future of Work, HR and Recruitment).

**Live demo (Render):** https://ai-powered-recuriment-agent.onrender.com
The demo runs on Render's free tier, so the first load can take up to a minute. Data on the demo may reset when it restarts.

---

## Deployment Status

This project is designed to run on a **Vultr Cloud Compute VM** (see [Vultr Architecture and Deployment Plan](#vultr-architecture-and-deployment-plan)).

The Vultr hackathon credit pool was exhausted before we could activate a Vultr account: Vultr required payment verification, and the gift codes had already been claimed. We raised this with the organizers in a ticket on the lablab Discord. They advised us to submit our GitHub repository, demo video and slides before the deadline and to state this reason in the README and the submission description.

**As an alternative, we deployed a temporary demo on Render. It is not a Vultr deployment.** We will move the app to Vultr as soon as credits are available, and we will update this section when that happens.

---

## The Problem

Small companies, placement offices and student societies often receive hundreds of resumes for a single role. Screening them by hand is slow and inconsistent, and small teams cannot afford recruiting software.

## How It Works

### Recruiter side
1. Register as a Recruiter and log in.
2. Post a job: title, department, location, employment type, minimum experience, required skills and description. Jobs can be edited, opened or closed, and deleted.
3. When applicants apply, the AI screens each resume automatically.
4. View the ranked applicant list for each job, with score bars and filters by keyword, score range and status.
5. Read the AI explanation for each candidate: 0-100 score, short justification, matching skills, missing skills.
6. Shortlist, put on hold or reject candidates, and add internal notes.
7. Generate tailored interview questions (3 technical, 2 behavioral) for a candidate, and regenerate them if needed.
8. Use the dashboard (active jobs, total applicants, average score, shortlisted count, applications per job, status distribution, common skills) and export the ranked list as CSV or PDF.

### Applicant side
1. Register as an Applicant, then browse and search open jobs.
2. Apply with a PDF or DOCX resume (maximum 10 MB).
3. See the match score, the matching skills and the missing skills.
4. Get AI feedback on how to improve the resume for that role.
5. Track application status and receive status emails.

### AI Tools page (use the AI separately)
Anyone can use these without posting a job or applying:
- **Resume Screening:** enter a target role and required skills, upload a resume, get a score, summary and skill gaps.
- **Interview Questions:** enter a role, candidate skills and a job description, get tailored questions.
- **Resume Feedback:** enter a target role and upload a resume, get suggestions and an estimated match score.

### The AI workflow
Extract text, parse into structured fields (name, contact, skills, education, experience, projects), score against the job, rank, then prepare questions and feedback. Each step stores real results in the database.

---

## Technology Stack

| Area | Technology | Used for |
|---|---|---|
| Backend | Python 3, Flask | Routes, sessions, uploads, application logic |
| Database | SQLite, Flask-SQLAlchemy | Users, jobs, applications, scores, email log |
| Authentication | Flask-Login, Werkzeug | Role-based login, password hashing |
| Frontend | HTML5, CSS3, Bootstrap 5, Bootstrap Icons, JavaScript | Responsive interface |
| Charts | Chart.js | Dashboard charts |
| AI (primary) | Google Gemini API (`google-genai`) | Parsing, scoring, explanations, questions, feedback |
| AI (fallback) | Groq API (`groq`) | Used when Gemini is rate-limited or fails |
| Resume parsing | PyMuPDF (`fitz`), python-docx | Text from PDF and DOCX |
| Automation | APScheduler | Daily recruiter digest job |
| Email | Python `smtplib` with Gmail SMTP | Status emails and digests |
| Reports | ReportLab, Python `csv` | PDF and CSV exports |
| Development | Antigravity, VS Code, Git, GitHub | Building and version control |
| Demo hosting | Render (free tier) | Temporary public demo |
| Planned hosting | Vultr Cloud Compute | See deployment plan below |

### AI reliability
The engine has three layers: Google Gemini first, Groq as a fallback, and a built-in rule-based skill matcher if both are unavailable. If email settings are missing, messages are recorded in an `EmailLog` table instead of being sent.

---

## Vultr Architecture and Deployment Plan

Vultr is intended to be the central backend, not static hosting.

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

The VM would host the web app, database, resume storage, scheduler and workflow orchestration. API keys would be kept in environment variables on the server.

### Planned deployment steps (Ubuntu VM)

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx git
git clone <this-repository-url> app && cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt gunicorn
cp .env.example .env          # then edit .env with real keys
python seed_data.py           # optional demo data
gunicorn -w 1 -b 127.0.0.1:8000 "run:app"
```

Use one gunicorn worker so the scheduler does not send duplicate digests. Then configure Nginx or Caddy to proxy ports 80 and 443 to `127.0.0.1:8000`, and run gunicorn as a systemd service.

> This plan has not been run on Vultr yet (see Deployment Status).

---

## Render Demo Deployment

The temporary demo uses these Render settings:

| Setting | Value |
|---|---|
| Service type | Web Service (Python 3, Free instance) |
| Build command | `pip install -r requirements.txt` |
| Start command | `mkdir -p data uploads/resumes && python seed_data.py && gunicorn -w 1 -b 0.0.0.0:$PORT "run:app"` |
| Environment variables | `PYTHON_VERSION`, `SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY` |

Render's free filesystem resets on restart, so the start command re-seeds the demo data each time.

---

## Quick Start (Local)

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

These accounts are created by `seed_data.py` for demos only. Change or remove them before any real deployment.

| Role | Email | Password |
|---|---|---|
| Recruiter | `recruiter@smarthire.ai` | `password123` |
| Applicant | `ayesha@example.com` | `password123` |
| Applicant | `bilal@example.com` | `password123` |

To generate sample resumes for testing:
```bash
python generate_sample_resumes.py
```
Use sample or fictional resumes for demos, never real people's data.

---

## Containment and Safety

- Uploads are validated for file type (PDF, DOCX) and size (10 MB maximum).
- Resume files are only parsed as text and are never executed.
- API keys and mail credentials live in environment variables, not in the code.
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
| Shortlisted / high match (70-100) | Green `#16A34A` |
| On hold / medium match (40-69) | Amber `#F59E0B` |
| Rejected / low match (0-39) | Red `#DC2626` |
| Applied / new | Sky Blue `#0EA5E9` |
| Background / surfaces / borders | `#F8FAFC` / `#FFFFFF` / `#E2E8F0` |
| Body text / muted text | `#1E293B` / `#64748B` |

---

## License

MIT. See the `LICENSE` file.
