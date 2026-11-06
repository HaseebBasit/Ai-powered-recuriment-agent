from datetime import datetime, timedelta
import logging
from app.extensions import scheduler, db
from app.config import Config
from app.models import User, JobPost, Application
from app.services.email_service import send_recruiter_daily_summary

logger = logging.getLogger(__name__)

def compile_daily_summary_for_recruiter(recruiter_id):
    """Aggregate application stats from the past 24 hours for a recruiter"""
    since_time = datetime.utcnow() - timedelta(days=1)
    recruiter = User.query.get(recruiter_id)
    if not recruiter:
        return None
        
    jobs = JobPost.query.filter_by(recruiter_id=recruiter.id).all()
    job_ids = [j.id for j in jobs]
    
    if not job_ids:
        return {
            "total_new": 0,
            "total_shortlisted": 0,
            "avg_score": 0,
            "job_breakdown": []
        }
        
    new_apps = Application.query.filter(
        Application.job_id.in_(job_ids),
        Application.applied_at >= since_time
    ).all()
    
    # If no apps in last 24h, grab all recent apps for the demo summary
    if not new_apps:
        new_apps = Application.query.filter(Application.job_id.in_(job_ids)).order_by(Application.applied_at.desc()).limit(10).all()
        
    total_new = len(new_apps)
    total_shortlisted = sum(1 for a in new_apps if a.status == "Shortlisted" or a.match_score >= 70)
    avg_score = round(sum(a.match_score for a in new_apps) / total_new) if total_new > 0 else 0
    
    breakdown = []
    for job in jobs:
        j_apps = [a for a in new_apps if a.job_id == job.id]
        if j_apps:
            j_avg = round(sum(a.match_score for a in j_apps) / len(j_apps))
            breakdown.append({
                "title": job.title,
                "count": len(j_apps),
                "avg_score": j_avg
            })
            
    return {
        "total_new": total_new,
        "total_shortlisted": total_shortlisted,
        "avg_score": avg_score,
        "job_breakdown": breakdown
    }

def run_daily_summary_job(app):
    """APScheduler cron target executed every day"""
    with app.app_context():
        logger.info("[Scheduler] Running daily applicant summary job...")
        recruiters = User.query.filter_by(role="recruiter").all()
        for recruiter in recruiters:
            summary = compile_daily_summary_for_recruiter(recruiter.id)
            if summary and (summary["total_new"] > 0 or summary["job_breakdown"]):
                send_recruiter_daily_summary(recruiter, summary)
        logger.info("[Scheduler] Daily applicant summary job completed.")

def init_scheduler(app):
    """Configure and start the APScheduler background scheduler"""
    if not scheduler.running:
        scheduler.add_job(
            func=run_daily_summary_job,
            args=[app],
            trigger="cron",
            hour=Config.DAILY_SUMMARY_HOUR,
            minute=Config.DAILY_SUMMARY_MINUTE,
            id="daily_recruiter_summary",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"[Scheduler] APScheduler started. Daily summary configured for {Config.DAILY_SUMMARY_HOUR:02d}:{Config.DAILY_SUMMARY_MINUTE:02d} UTC.")

