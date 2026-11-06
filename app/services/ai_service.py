import os
import re
import json
import logging
from app.config import Config
from app.models import SystemConfig

logger = logging.getLogger(__name__)

# Predefined common technical skills taxonomy for extraction and heuristics
SKILLS_TAXONOMY = [
    "python", "flask", "django", "fastapi", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "nodejs", "express", "html", "css", "bootstrap", "tailwind", "sql", "sqlite",
    "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "github", "gitlab", "ci/cd", "rest api", "restful api", "graphql", "microservices",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "data analysis", "data science", "agile", "scrum",
    "jira", "linux", "c++", "c#", "java", "spring boot", "php", "laravel", "ruby", "rails"
]

def get_active_keys():
    """Retrieve Gemini and Groq API keys from DB or environment"""
    from flask import has_app_context
    gemini_key = None
    groq_key = None
    if has_app_context():
        try:
            gemini_key = SystemConfig.get_value("GEMINI_API_KEY")
            groq_key = SystemConfig.get_value("GROQ_API_KEY")
        except Exception:
            pass
    return gemini_key or Config.GEMINI_API_KEY, groq_key or Config.GROQ_API_KEY

def call_gemini(prompt, api_key):
    """Call Google Gemini API using google-genai SDK or direct REST API"""
    models_to_try = ["gemini-3.8-flash", "gemini-2.0-flash"]
    last_err = None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except Exception as me:
                last_err = me
                logger.warning(f"Gemini model {model_name} failed: {me}")
                continue
    except Exception as e:
        last_err = e
    if last_err:
        raise last_err

def call_groq(prompt, api_key):
    """Call Groq API as free fallback"""
    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    last_err = None
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        for model_name in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are SmartHire AI, an expert ATS resume evaluator and recruiting assistant. Always respond with strict JSON or cleanly formatted responses as requested."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model_name,
                    temperature=0.2,
                )
                if chat_completion and chat_completion.choices:
                    return chat_completion.choices[0].message.content
            except Exception as me:
                last_err = me
                logger.warning(f"Groq model {model_name} failed: {me}")
                continue
    except Exception as e:
        last_err = e
    if last_err:
        raise last_err

def query_ai_with_fallback(prompt):
    """
    Query Gemini first; if it fails or rate limits, switch to Groq;
    if both fail or no keys, return None so heuristic parser is triggered.
    """
    gemini_key, groq_key = get_active_keys()
    
    # 1. Try Gemini
    if gemini_key and gemini_key.strip():
        try:
            logger.info("Attempting AI generation via Google Gemini...")
            result = call_gemini(prompt, gemini_key.strip())
            if result:
                return result
        except Exception as e:
            logger.warning(f"Google Gemini failed or rate-limited: {e}. Switching to Groq fallback...")
            
    # 2. Try Groq fallback
    if groq_key and groq_key.strip():
        try:
            logger.info("Attempting AI generation via Groq API...")
            result = call_groq(prompt, groq_key.strip())
            if result:
                return result
        except Exception as e:
            logger.warning(f"Groq API fallback failed: {e}")
            
    return None

# ==========================================
# Intelligent Deterministic Heuristic Parsers
# ==========================================

def heuristic_extract_contact_info(text):
    """Extract contact information and basic entities from resume text"""
    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else ""
    
    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else ""
    
    # Name: Typically the first line or near contact info
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    name = ""
    for line in lines[:5]:
        # Filter out emails, phones, URLs, and generic headers
        if (len(line) < 40 and not any(char in line for char in ["@", "http", "www.", "/", "\\", ":", "|"])
            and not any(header in line.lower() for header in ["resume", "curriculum vitae", "cv", "summary", "contact", "profile"])):
            name = line
            break
    if not name and lines:
        name = lines[0][:40]
        
    return name, email, phone

def heuristic_extract_skills(text):
    """Identify skills present in resume text against skills taxonomy"""
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_TAXONOMY:
        # Match whole word or exact token
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title() if len(skill) > 3 and not skill.isupper() else skill.upper())
    return list(dict.fromkeys(found_skills))

def heuristic_extract_experience_years(text):
    """Estimate experience years from text"""
    exp_matches = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?', text, re.IGNORECASE)
    if exp_matches:
        try:
            return max(int(m) for m in exp_matches)
        except Exception:
            pass
    # Estimate based on date ranges (e.g. 2021 - 2024)
    year_matches = re.findall(r'(20\d\d|19\d\d)\s*(?:-|to|–)\s*(20\d\d|present|current)', text, re.IGNORECASE)
    total_est = 0
    import datetime
    current_year = datetime.datetime.now().year
    for start, end in year_matches:
        try:
            s = int(start)
            e = current_year if end.lower() in ("present", "current") else int(end)
            if 0 <= (e - s) <= 25:
                total_est += (e - s)
        except Exception:
            pass
    return max(total_est, 1) if year_matches else 1

def heuristic_extract_education(text):
    """Extract education degree hints"""
    degrees = []
    edu_keywords = ["Bachelor", "Master", "B.S.", "B.Sc", "M.S.", "M.Sc", "B.Tech", "M.Tech", "Ph.D", "Diploma", "Associate"]
    for kw in edu_keywords:
        match = re.search(rf'({kw}[^\n,\.]{{0,60}})', text, re.IGNORECASE)
        if match:
            degrees.append(match.group(1).strip())
    return degrees if degrees else ["Relevant Higher Education / Technical Degree"]

# ==========================================
# Core AI Services
# ==========================================

def parse_resume(resume_text):
    """
    Parse resume into structured JSON:
    name, email, phone, skills, experience_years, education, projects, summary
    """
    prompt = f"""
    You are an expert ATS resume parser. Extract structured information from the following resume text.
    Return ONLY a valid JSON object with these exact keys:
    {{
        "name": "Candidate Full Name",
        "email": "Email Address",
        "phone": "Phone Number",
        "skills": ["Skill 1", "Skill 2", ...],
        "experience_years": 3,
        "education": ["Degree 1 at University", ...],
        "projects": ["Project 1 summary", ...],
        "summary": "2-3 sentence executive profile summary"
    }}

    RESUME TEXT:
    {resume_text[:4000]}
    """
    
    ai_raw = query_ai_with_fallback(prompt)
    if ai_raw:
        try:
            # Strip markdown json blocks
            cleaned = re.sub(r'```(?:json)?', '', ai_raw).strip()
            data = json.loads(cleaned)
            return data
        except Exception as e:
            logger.warning(f"Failed to parse AI JSON response: {e}. Using heuristic fallback.")

    # Heuristic Fallback
    name, email, phone = heuristic_extract_contact_info(resume_text)
    skills = heuristic_extract_skills(resume_text)
    exp_years = heuristic_extract_experience_years(resume_text)
    education = heuristic_extract_education(resume_text)
    
    return {
        "name": name or "Applicant",
        "email": email or "",
        "phone": phone or "",
        "skills": skills if skills else ["Python", "Problem Solving", "Web Development"],
        "experience_years": exp_years,
        "education": education,
        "projects": [f"Implemented technical applications using {', '.join(skills[:3]) if skills else 'modern tools'}."],
        "summary": f"Professional with approximately {exp_years} year(s) of experience possessing demonstrated knowledge in {', '.join(skills[:5]) if skills else 'software engineering'}."
    }

def screen_and_score_resume(resume_text, parsed_data, job_title, job_skills_list, job_min_exp, job_description):
    """
    Compare resume with job description and requirements.
    Calculates match score (0-100), justification, matching & missing skills, and applicant feedback.
    """
    prompt = f"""
    You are SmartHire AI, an ATS resume evaluator.
    Compare the candidate's resume with the target job posting.

    JOB DETAILS:
    - Job Title: {job_title}
    - Minimum Experience: {job_min_exp} years
    - Required Skills: {', '.join(job_skills_list)}
    - Description: {job_description[:1500]}

    CANDIDATE DETAILS:
    - Name: {parsed_data.get('name', 'Candidate')}
    - Extracted Skills: {', '.join(parsed_data.get('skills', []))}
    - Experience Years: {parsed_data.get('experience_years', 0)}
    - Education: {', '.join(parsed_data.get('education', []))}
    - Resume Excerpt: {resume_text[:2000]}

    Return ONLY a valid JSON object with the following keys:
    {{
        "match_score": 85,
        "match_justification": "Clear and concise explanation of strengths and gaps...",
        "matching_skills": ["Skill 1", "Skill 2"],
        "missing_skills": ["Skill 3", "Skill 4"],
        "ai_feedback": "Actionable, constructive tips for the applicant to improve their resume for this role",
        "suggested_status": "Shortlisted" 
    }}
    Note: match_score must be an integer between 0 and 100.
    Status logic: 70-100 = Shortlisted, 40-69 = On Hold, 0-39 = Rejected.
    """
    
    ai_raw = query_ai_with_fallback(prompt)
    if ai_raw:
        try:
            cleaned = re.sub(r'```(?:json)?', '', ai_raw).strip()
            data = json.loads(cleaned)
            score = int(data.get("match_score", 65))
            score = max(0, min(100, score))
            data["match_score"] = score
            if score >= 70:
                data["suggested_status"] = "Shortlisted"
            elif score >= 40:
                data["suggested_status"] = "On Hold"
            else:
                data["suggested_status"] = "Rejected"
            return data
        except Exception as e:
            logger.warning(f"Failed to parse AI scoring response: {e}. Using intelligent heuristic algorithm.")

    # Heuristic Scoring Engine
    candidate_skills_lower = [s.lower() for s in parsed_data.get("skills", [])]
    # Also check raw resume text for required skills
    raw_text_lower = resume_text.lower()
    
    matching_skills = []
    missing_skills = []
    
    for req in job_skills_list:
        req_clean = req.strip()
        req_lower = req_clean.lower()
        if req_lower in candidate_skills_lower or re.search(r'\b' + re.escape(req_lower) + r'\b', raw_text_lower):
            matching_skills.append(req_clean)
        else:
            missing_skills.append(req_clean)
            
    # Skill Match Ratio (up to 70 points)
    total_req = max(len(job_skills_list), 1)
    skill_ratio = len(matching_skills) / total_req
    skill_score = skill_ratio * 70
    
    # Experience Score (up to 20 points)
    candidate_exp = parsed_data.get("experience_years", 0)
    if job_min_exp <= 0:
        exp_score = 20
    else:
        exp_score = min(20, (candidate_exp / max(job_min_exp, 1)) * 20)
        
    # Text Relevancy / Baseline (up to 10 points)
    relevancy_score = 10 if any(word in raw_text_lower for word in job_title.lower().split()) else 5
    
    total_score = int(round(skill_score + exp_score + relevancy_score))
    total_score = max(15, min(98, total_score))
    
    if total_score >= 70:
        suggested_status = "Shortlisted"
        justification = (
            f"Strong profile match ({total_score}%). The candidate possesses {len(matching_skills)} out of {total_req} "
            f"core required competencies including {', '.join(matching_skills[:4])}. "
            f"Their background aligns well with the {job_min_exp}+ years experience requirement."
        )
    elif total_score >= 40:
        suggested_status = "On Hold"
        justification = (
            f"Moderate profile match ({total_score}%). Demonstrates key skills such as {', '.join(matching_skills[:3]) if matching_skills else 'foundational skills'}, "
            f"but lacks direct proof for required skills: {', '.join(missing_skills[:3]) if missing_skills else 'advanced competencies'}. Recommended for further review."
        )
    else:
        suggested_status = "Rejected"
        justification = (
            f"Low compatibility ({total_score}%). Significant skill and qualification gaps identified against role criteria. "
            f"Missing essential competencies: {', '.join(missing_skills[:4]) if missing_skills else 'required tech stack'}."
        )
        
    ai_feedback = (
        f"Key Recommendations for {job_title}:\n"
        f"1. Target Missing Competencies: Incorporate specific projects or coursework showcasing {', '.join(missing_skills[:3]) if missing_skills else 'specialized tools'}.\n"
        f"2. Quantify Outcomes: Strengthen your bullet points by adding measurable metrics (e.g., 'improved query speed by 35%' or 'served 10k users').\n"
        f"3. Tailor Keywords: Align your project descriptions with the exact keywords mentioned in the job description to improve automated screening."
    )
    
    return {
        "match_score": total_score,
        "match_justification": justification,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "ai_feedback": ai_feedback,
        "suggested_status": suggested_status
    }

def generate_tailored_interview_questions(resume_text, parsed_data, job_title, job_description):
    """
    Generate 5 tailored interview questions:
    3 Technical (based on job requirements and candidate's claimed skills)
    2 Behavioral (STAR method based on collaboration and problem-solving)
    """
    candidate_name = parsed_data.get("name", "Applicant")
    skills = parsed_data.get("skills", ["Python", "Web APIs"])
    skills_str = ", ".join(skills[:6])
    
    prompt = f"""
    You are an expert technical interviewer for the position '{job_title}'.
    Candidate Name: {candidate_name}
    Candidate Skills: {skills_str}
    Job Description: {job_description[:1000]}

    Generate exactly 5 tailored interview questions:
    - 3 specific technical questions directly testing their claimed skills against the job needs.
    - 2 behavioral questions evaluating problem-solving, collaboration, or handling project pressure.

    Return ONLY a JSON list of 5 question strings:
    [
        "1. Technical question...",
        "2. Technical question...",
        "3. Technical question...",
        "4. Behavioral question...",
        "5. Behavioral question..."
    ]
    """
    
    ai_raw = query_ai_with_fallback(prompt)
    if ai_raw:
        try:
            cleaned = re.sub(r'```(?:json)?', '', ai_raw).strip()
            data = json.loads(cleaned)
            if isinstance(data, list) and len(data) >= 3:
                return data
        except Exception as e:
            logger.warning(f"Failed to parse AI interview questions: {e}. Using tailored heuristic questions.")

    # Tailored Heuristic Questions matching brand guide examples:
    # E.g. "1. Explain how you would design a REST API for job postings in Flask."
    primary_skill = skills[0] if skills else "Python"
    secondary_skill = skills[1] if len(skills) > 1 else "REST APIs"
    third_skill = skills[2] if len(skills) > 2 else "SQL Database"
    
    return [
        f"1. Explain how you would design a scalable {secondary_skill} backend or service for '{job_title}' using {primary_skill}.",
        f"2. In your experience with {third_skill}, how do you optimize performance and handle high concurrent load or edge cases?",
        f"3. Walk us through a complex bug or architectural bottleneck you encountered while working with {primary_skill} and how you diagnosed it.",
        f"4. Describe a time you resolved a technical conflict or disagreement with a teammate regarding system architecture.",
        f"5. Tell us about a project where deadlines were tight and requirements shifted; how did you prioritize tasks and deliver quality results?"
    ]

