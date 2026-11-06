import os
import json
from collections import Counter
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import JobPost, Application, EmailLog, SystemConfig, User, ContactMessage
from app.services.report_service import generate_applicants_csv, generate_applicants_pdf
from app.services.email_service import send_status_update_email, send_recruiter_daily_summary
from app.services.scheduler_service import compile_daily_summary_for_recruiter
from app.services.ai_service import generate_tailored_interview_questions, query_ai_with_fallback

recruiter_bp = Blueprint("recruiter", __name__, url_prefix="/recruiter")

def recruiter_required():
    if not current_user.is_authenticated or not current_user.is_recruiter:
        abort(403)

@recruiter_bp.before_request
def check_access():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if not current_user.is_recruiter:
        flash("Access restricted to recruiters only.", "danger")
        return redirect(url_for("applicant.dashboard"))

@recruiter_bp.route("/dashboard")
def dashboard():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).order_by(JobPost.created_at.desc()).all()
    job_ids = [j.id for j in jobs]
    
    applications = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []
    
    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs if j.status == "Open")
    total_applicants = len(applications)
    
    avg_score = round(sum(a.match_score for a in applications) / total_applicants) if total_applicants else 0
    shortlisted_count = sum(1 for a in applications if a.status == "Shortlisted" or a.match_score >= 70)
    on_hold_count = sum(1 for a in applications if a.status == "On Hold" or (40 <= a.match_score < 70))
    rejected_count = sum(1 for a in applications if a.status == "Rejected" or a.match_score < 40)
    interviews_count = sum(1 for a in applications if a.status == "Shortlisted")
    applied_count = sum(1 for a in applications if a.status == "Applied")
    
    # Skills aggregation across applicants
    all_skills = []
    for app in applications:
        all_skills.extend(app.get_matching_skills_list())
        parsed = app.get_parsed_dict()
        if "skills" in parsed and isinstance(parsed["skills"], list):
            all_skills.extend(parsed["skills"])
    skill_counts = Counter(all_skills).most_common(8)
    
    recent_apps = sorted(applications, key=lambda a: a.applied_at, reverse=True)[:10]
    
    # Applications per job data for chart
    job_chart_labels = [j.title[:20] for j in jobs[:6]]
    job_chart_counts = [len(j.applications) for j in jobs[:6]]
    
    return render_template(
        "recruiter/dashboard.html",
        jobs=jobs,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applicants=total_applicants,
        avg_score=avg_score,
        shortlisted_count=shortlisted_count,
        on_hold_count=on_hold_count,
        rejected_count=rejected_count,
        interviews_count=interviews_count,
        applied_count=applied_count,
        recent_apps=recent_apps,
        skill_counts=skill_counts,
        job_chart_labels=json.dumps(job_chart_labels),
        job_chart_counts=json.dumps(job_chart_counts),
        status_counts=json.dumps([shortlisted_count, on_hold_count, rejected_count, applied_count])
    )

@recruiter_bp.route("/jobs")
def jobs_list():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).order_by(JobPost.created_at.desc()).all()
    return render_template("recruiter/jobs.html", jobs=jobs)

@recruiter_bp.route("/jobs/new", methods=["GET", "POST"])
def job_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        department = request.form.get("department", "Engineering").strip()
        location = request.form.get("location", "Remote").strip()
        employment_type = request.form.get("employment_type", "Full-time")
        min_experience = int(request.form.get("min_experience", 0))
        required_skills = request.form.get("required_skills", "").strip()
        description = request.form.get("description", "").strip()
        deadline_str = request.form.get("deadline", "").strip()
        
        if not title or not required_skills or not description:
            flash("Title, Required Skills, and Description are required.", "warning")
            return render_template("recruiter/job_form.html", action="Create", job=None)
            
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            except Exception:
                pass
                
        new_job = JobPost(
            recruiter_id=current_user.id,
            title=title,
            department=department,
            location=location,
            employment_type=employment_type,
            min_experience=min_experience,
            required_skills=required_skills,
            description=description,
            status="Open",
            deadline=deadline
        )
        db.session.add(new_job)
        db.session.commit()
        
        flash(f"Job posting '{title}' created successfully!", "success")
        return redirect(url_for("recruiter.jobs_list"))
        
    return render_template("recruiter/job_form.html", action="Create", job=None)

@recruiter_bp.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    
    # Ranked applicants: highest match score first
    ranked_applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    return render_template("recruiter/job_detail.html", job=job, applications=ranked_applications)

@recruiter_bp.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def job_edit(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        job.title = request.form.get("title", job.title).strip()
        job.department = request.form.get("department", job.department).strip()
        job.location = request.form.get("location", job.location).strip()
        job.employment_type = request.form.get("employment_type", job.employment_type)
        job.min_experience = int(request.form.get("min_experience", job.min_experience))
        job.required_skills = request.form.get("required_skills", job.required_skills).strip()
        job.description = request.form.get("description", job.description).strip()
        job.status = request.form.get("status", job.status)
        
        deadline_str = request.form.get("deadline", "").strip()
        if deadline_str:
            try:
                job.deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            except Exception:
                pass
                
        db.session.commit()
        flash(f"Job '{job.title}' updated successfully.", "success")
        return redirect(url_for("recruiter.job_detail", job_id=job.id))
        
    return render_template("recruiter/job_form.html", action="Edit", job=job)

@recruiter_bp.route("/jobs/<int:job_id>/toggle-status", methods=["POST"])
def job_toggle_status(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    job.status = "Closed" if job.status == "Open" else "Open"
    db.session.commit()
    flash(f"Job status changed to {job.status}.", "info")
    return redirect(url_for("recruiter.jobs_list"))

@recruiter_bp.route("/jobs/<int:job_id>/delete", methods=["POST"])
def job_delete(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f"Job '{title}' and all associated applications were permanently removed.", "info")
    return redirect(url_for("recruiter.jobs_list"))

@recruiter_bp.route("/applicants")
def all_applicants():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).all()
    job_ids = [j.id for j in jobs]
    
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    
    apps_query = Application.query.filter(Application.job_id.in_(job_ids)) if job_ids else Application.query.filter_by(id=-1)
    
    if q:
        search = f"%{q}%"
        apps_query = apps_query.filter(
            (Application.applicant_name.ilike(search)) |
            (Application.applicant_email.ilike(search)) |
            (Application.matching_skills.ilike(search))
        )
    if status_filter:
        apps_query = apps_query.filter(Application.status == status_filter)
        
    applications = apps_query.order_by(Application.match_score.desc()).all()
    
    return render_template(
        "recruiter/applicants_list.html",
        applications=applications,
        query=q,
        status_filter=status_filter,
        jobs=jobs
    )

@recruiter_bp.route("/shortlisted")
def shortlisted_candidates():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).all()
    job_ids = [j.id for j in jobs]
    
    apps = Application.query.filter(
        Application.job_id.in_(job_ids),
        (Application.status == "Shortlisted") | (Application.match_score >= 70)
    ).order_by(Application.match_score.desc()).all() if job_ids else []
    
    return render_template(
        "recruiter/shortlisted.html",
        applications=apps,
        jobs=jobs
    )

@recruiter_bp.route("/reports")
def reports_hub():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).all()
    job_ids = [j.id for j in jobs]
    applications = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []
    
    return render_template("recruiter/reports.html", jobs=jobs, total_apps=len(applications))

@recruiter_bp.route("/messages")
def messages():
    contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("recruiter/messages.html", messages=contact_messages)

@recruiter_bp.route("/jobs/<int:job_id>/export/csv")
def export_csv(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    csv_content = generate_applicants_csv(job, applications)
    filename = f"SmartHire_Ranked_Applicants_Job_{job.id}.csv"
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@recruiter_bp.route("/jobs/<int:job_id>/export/pdf")
def export_pdf(job_id):
    job = JobPost.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    pdf_buffer = generate_applicants_pdf(job, applications)
    filename = f"SmartHire_Applicant_Evaluation_Report_Job_{job.id}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@recruiter_bp.route("/applications/<int:app_id>")
def applicant_detail(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.recruiter_id != current_user.id:
        abort(403)
        
    parsed_info = application.get_parsed_dict()
    matching_skills = application.get_matching_skills_list()
    missing_skills = application.get_missing_skills_list()
    interview_questions = application.get_interview_questions_list()
    
    return render_template(
        "recruiter/applicant_detail.html",
        application=application,
        job=application.job,
        parsed_info=parsed_info,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        interview_questions=interview_questions
    )

@recruiter_bp.route("/applications/<int:app_id>/status", methods=["POST"])
def update_applicant_status(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.recruiter_id != current_user.id:
        abort(403)
        
    new_status = request.form.get("status")
    if new_status in ["Applied", "Shortlisted", "On Hold", "Rejected"]:
        old_status = application.status
        application.status = new_status
        db.session.commit()
        
        # Send status update email if status actually changed
        if old_status != new_status:
            send_status_update_email(application, new_status)
            
        flash(f"Application status updated to '{new_status}' and notification sent.", "success")
    else:
        flash("Invalid status selected.", "warning")
        
    return redirect(url_for("recruiter.applicant_detail", app_id=application.id))

@recruiter_bp.route("/applications/<int:app_id>/notes", methods=["POST"])
def save_recruiter_notes(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.recruiter_id != current_user.id:
        abort(403)
        
    notes = request.form.get("recruiter_notes", "").strip()
    application.recruiter_notes = notes
    db.session.commit()
    
    flash("Recruiter internal notes saved successfully.", "success")
    return redirect(url_for("recruiter.applicant_detail", app_id=application.id))

@recruiter_bp.route("/applications/<int:app_id>/generate-questions", methods=["POST"])
def regenerate_interview_questions(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.recruiter_id != current_user.id:
        abort(403)
        
    questions = generate_tailored_interview_questions(
        resume_text=application.extracted_text or "",
        parsed_data=application.get_parsed_dict(),
        job_title=application.job.title,
        job_description=application.job.description
    )
    
    application.interview_questions = json.dumps(questions)
    db.session.commit()
    
    flash("Fresh tailored interview questions generated via AI!", "success")
    return redirect(url_for("recruiter.applicant_detail", app_id=application.id))

@recruiter_bp.route("/applications/<int:app_id>/resume")
def download_resume(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.recruiter_id != current_user.id and (not current_user.is_authenticated or current_user.id != application.applicant_id):
        abort(403)
        
    if not os.path.exists(application.resume_path):
        flash("Resume file could not be found on server storage.", "danger")
        return redirect(url_for("recruiter.applicant_detail", app_id=application.id))
        
    return send_file(
        application.resume_path,
        as_attachment=True,
        download_name=application.resume_filename
    )

@recruiter_bp.route("/emails")
def emails_log():
    jobs = JobPost.query.filter_by(recruiter_id=current_user.id).all()
    job_ids = [j.id for j in jobs]
    
    logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(100).all()
    return render_template("recruiter/emails_log.html", logs=logs)

@recruiter_bp.route("/daily-summary/trigger", methods=["POST"])
def trigger_daily_summary_manual():
    summary_data = compile_daily_summary_for_recruiter(current_user.id)
    success = send_recruiter_daily_summary(current_user, summary_data)
    
    if success:
        flash(f"Daily digest summary email successfully dispatched to {current_user.email}!", "success")
    else:
        flash(f"Daily summary compiled and logged (check Automated Communications log).", "info")
        
    return redirect(url_for("recruiter.emails_log"))

@recruiter_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        gemini_key = request.form.get("gemini_key", "").strip()
        groq_key = request.form.get("groq_key", "").strip()
        mail_username = request.form.get("mail_username", "").strip()
        mail_password = request.form.get("mail_password", "").strip()
        
        if gemini_key:
            SystemConfig.set_value("GEMINI_API_KEY", gemini_key)
        if groq_key:
            SystemConfig.set_value("GROQ_API_KEY", groq_key)
        if mail_username:
            SystemConfig.set_value("MAIL_USERNAME", mail_username)
        if mail_password:
            SystemConfig.set_value("MAIL_PASSWORD", mail_password)
            
        flash("AI & SMTP System configuration saved successfully.", "success")
        return redirect(url_for("recruiter.settings"))
        
    gemini_key = SystemConfig.get_value("GEMINI_API_KEY", "")
    groq_key = SystemConfig.get_value("GROQ_API_KEY", "")
    mail_username = SystemConfig.get_value("MAIL_USERNAME", "")
    
    return render_template(
        "recruiter/settings.html",
        gemini_key=gemini_key,
        groq_key=groq_key,
        mail_username=mail_username
    )
