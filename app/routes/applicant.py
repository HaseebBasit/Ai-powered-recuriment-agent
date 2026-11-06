import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import JobPost, Application, SavedJob, User
from app.services.resume_parser import extract_resume_text
from app.services.ai_service import parse_resume, screen_and_score_resume, generate_tailored_interview_questions
from app.services.email_service import send_application_received_email

applicant_bp = Blueprint("applicant", __name__, url_prefix="/applicant")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@applicant_bp.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=url_for("applicant.dashboard")))
        
    tab = request.args.get("tab", "applications")
    
    # User applications
    my_apps = Application.query.filter_by(applicant_id=current_user.id).order_by(Application.applied_at.desc()).all()
    
    # Saved jobs
    saved_records = SavedJob.query.filter_by(user_id=current_user.id).order_by(SavedJob.saved_at.desc()).all()
    saved_jobs = [s.job for s in saved_records]
    saved_job_ids = [s.job_id for s in saved_records]
    
    # Statistics
    total_apps = len(my_apps)
    shortlisted_apps = sum(1 for a in my_apps if a.status == "Shortlisted" or a.match_score >= 70)
    pending_apps = sum(1 for a in my_apps if a.status in ["Applied", "On Hold"])
    rejected_apps = sum(1 for a in my_apps if a.status == "Rejected")
    
    return render_template(
        "applicant/dashboard.html",
        applications=my_apps,
        saved_jobs=saved_jobs,
        saved_job_ids=saved_job_ids,
        total_apps=total_apps,
        shortlisted_apps=shortlisted_apps,
        pending_apps=pending_apps,
        rejected_apps=rejected_apps,
        tab=tab
    )

@applicant_bp.route("/jobs")
def jobs_list():
    query = request.args.get("q", "").strip()
    location_filter = request.args.get("location", "").strip()
    job_types = request.args.getlist("type")  # Full Time, Part Time, Remote, Internship, Contract
    exp_levels = request.args.getlist("exp_level") # entry, mid, senior
    department_filter = request.args.get("dept", "").strip()
    
    jobs_query = JobPost.query.filter_by(status="Open")
    
    if query:
        search_filter = f"%{query}%"
        jobs_query = jobs_query.filter(
            (JobPost.title.ilike(search_filter)) |
            (JobPost.required_skills.ilike(search_filter)) |
            (JobPost.department.ilike(search_filter)) |
            (JobPost.description.ilike(search_filter))
        )
        
    if location_filter:
        loc_pattern = f"%{location_filter}%"
        jobs_query = jobs_query.filter(JobPost.location.ilike(loc_pattern))
        
    if job_types:
        type_filters = [JobPost.employment_type.ilike(f"%{t}%") for t in job_types]
        from sqlalchemy import or_
        jobs_query = jobs_query.filter(or_(*type_filters))
        
    if exp_levels:
        from sqlalchemy import or_
        exp_conditions = []
        for el in exp_levels:
            if el == "entry":
                exp_conditions.append(JobPost.min_experience <= 1)
            elif el == "mid":
                exp_conditions.append((JobPost.min_experience >= 2) & (JobPost.min_experience <= 4))
            elif el == "senior":
                exp_conditions.append(JobPost.min_experience >= 5)
        if exp_conditions:
            jobs_query = jobs_query.filter(or_(*exp_conditions))
            
    if department_filter:
        jobs_query = jobs_query.filter(JobPost.department.ilike(f"%{department_filter}%"))
            
    jobs = jobs_query.order_by(JobPost.created_at.desc()).all()
    
    # Get user's saved job ids if logged in
    saved_job_ids = []
    if current_user.is_authenticated:
        saved_records = SavedJob.query.filter_by(user_id=current_user.id).all()
        saved_job_ids = [s.job_id for s in saved_records]
        
    # Get departments for filter sidebar
    available_departments = [d[0] for d in db.session.query(JobPost.department).distinct().all() if d[0]]
    
    return render_template(
        "applicant/jobs.html",
        jobs=jobs,
        query=query,
        location=location_filter,
        job_types=job_types,
        exp_levels=exp_levels,
        dept=department_filter,
        departments=available_departments,
        saved_job_ids=saved_job_ids
    )

@applicant_bp.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = JobPost.query.get_or_404(job_id)
    has_applied = False
    is_saved = False
    existing_app = None
    
    if current_user.is_authenticated:
        existing_app = Application.query.filter_by(job_id=job.id, applicant_id=current_user.id).first()
        has_applied = existing_app is not None
        saved_rec = SavedJob.query.filter_by(job_id=job.id, user_id=current_user.id).first()
        is_saved = saved_rec is not None
        
    return render_template(
        "applicant/job_detail.html",
        job=job,
        has_applied=has_applied,
        is_saved=is_saved,
        application=existing_app
    )

@applicant_bp.route("/jobs/<int:job_id>/save", methods=["POST"])
def toggle_save_job(job_id):
    if not current_user.is_authenticated:
        flash("Please log in to save job postings.", "info")
        return redirect(url_for("auth.login", next=url_for("applicant.job_detail", job_id=job_id)))
        
    job = JobPost.query.get_or_404(job_id)
    saved = SavedJob.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    
    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash(f"Removed '{job.title}' from your saved jobs.", "info")
    else:
        new_save = SavedJob(user_id=current_user.id, job_id=job.id)
        db.session.add(new_save)
        db.session.commit()
        flash(f"Saved '{job.title}' to your portfolio!", "success")
        
    next_page = request.referrer or url_for("applicant.job_detail", job_id=job_id)
    return redirect(next_page)

@applicant_bp.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
def apply(job_id):
    job = JobPost.query.get_or_404(job_id)
    if job.status != "Open":
        flash("This job posting is currently closed for applications.", "warning")
        return redirect(url_for("applicant.job_detail", job_id=job.id))
        
    if current_user.is_authenticated:
        existing = Application.query.filter_by(job_id=job.id, applicant_id=current_user.id).first()
        if existing:
            flash("You have already applied for this position. Here is your evaluation feedback.", "info")
            return redirect(url_for("applicant.feedback", app_id=existing.id))
            
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        resume_file = request.files.get("resume")
        
        if not name or not email:
            flash("Name and email are required.", "warning")
            return render_template("applicant/apply.html", job=job)
            
        if not resume_file or resume_file.filename == "":
            flash("Please upload your resume in PDF or DOCX format.", "warning")
            return render_template("applicant/apply.html", job=job)
            
        if not allowed_file(resume_file.filename):
            flash("Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).", "danger")
            return render_template("applicant/apply.html", job=job)
            
        # Secure filename & save to disk
        original_fname = secure_filename(resume_file.filename)
        save_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(save_dir, exist_ok=True)
        unique_fname = f"{uuid.uuid4().hex[:12]}_{original_fname}"
        save_path = os.path.join(save_dir, unique_fname)
        
        resume_file.save(save_path)
        
        # 1. Text Extraction
        extracted_text = extract_resume_text(save_path)
        if not extracted_text:
            extracted_text = f"Resume submitted by {name} ({email}). Technical candidate."
            
        # 2. AI Parsing
        parsed_data = parse_resume(extracted_text)
        
        # Override name/email if user provided explicit values in form
        if name:
            parsed_data["name"] = name
        if email:
            parsed_data["email"] = email
        if phone:
            parsed_data["phone"] = phone
            
        # 3. AI Screening & Match Scoring
        screening = screen_and_score_resume(
            resume_text=extracted_text,
            parsed_data=parsed_data,
            job_title=job.title,
            job_skills_list=job.get_skills_list(),
            job_min_exp=job.min_experience,
            job_description=job.description
        )
        
        # 4. Generate Tailored Interview Questions
        interview_questions = generate_tailored_interview_questions(
            resume_text=extracted_text,
            parsed_data=parsed_data,
            job_title=job.title,
            job_description=job.description
        )
        
        # 5. Save Application Record
        application = Application(
            job_id=job.id,
            applicant_id=current_user.id if current_user.is_authenticated else None,
            applicant_name=name,
            applicant_email=email,
            applicant_phone=phone,
            resume_filename=original_fname,
            resume_path=save_path,
            extracted_text=extracted_text,
            parsed_data=json.dumps(parsed_data),
            match_score=screening.get("match_score", 60),
            match_justification=screening.get("match_justification", ""),
            matching_skills=json.dumps(screening.get("matching_skills", [])),
            missing_skills=json.dumps(screening.get("missing_skills", [])),
            status=screening.get("suggested_status", "Applied"),
            ai_feedback=screening.get("ai_feedback", ""),
            interview_questions=json.dumps(interview_questions),
            applied_at=datetime.utcnow()
        )
        
        db.session.add(application)
        db.session.commit()
        
        # 6. Automated Email Notification
        send_application_received_email(application)
        
        flash("Application successfully submitted and analyzed by AI-Powered Recruitment Agent!", "success")
        return redirect(url_for("applicant.feedback", app_id=application.id))
        
    return render_template("applicant/apply.html", job=job)

@applicant_bp.route("/applications/<int:app_id>/feedback")
def feedback(app_id):
    application = Application.query.get_or_404(app_id)
    if current_user.is_authenticated and application.applicant_id and application.applicant_id != current_user.id:
        if not current_user.is_recruiter:
            abort(403)
            
    parsed_info = application.get_parsed_dict()
    matching_skills = application.get_matching_skills_list()
    missing_skills = application.get_missing_skills_list()
    
    return render_template(
        "applicant/feedback.html",
        application=application,
        job=application.job,
        parsed_info=parsed_info,
        matching_skills=matching_skills,
        missing_skills=missing_skills
    )
