import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from app.config import Config
from app.extensions import db
from app.models import EmailLog, SystemConfig

logger = logging.getLogger(__name__)

def get_smtp_config():
    """Retrieve SMTP settings from SystemConfig or Config"""
    server = SystemConfig.get_value("MAIL_SERVER") or Config.MAIL_SERVER
    port = int(SystemConfig.get_value("MAIL_PORT") or Config.MAIL_PORT)
    username = SystemConfig.get_value("MAIL_USERNAME") or Config.MAIL_USERNAME
    password = SystemConfig.get_value("MAIL_PASSWORD") or Config.MAIL_PASSWORD
    sender = SystemConfig.get_value("MAIL_DEFAULT_SENDER") or Config.MAIL_DEFAULT_SENDER
    use_tls = Config.MAIL_USE_TLS
    return server, port, username, password, sender, use_tls

def send_email(to_email, subject, html_body, plain_body=None, job_id=None, application_id=None):
    """
    Send an email via Gmail SMTP. If SMTP credentials are missing or network fails,
    cleanly records the email into EmailLog so notifications are never lost and the app never crashes.
    """
    server, port, username, password, sender, use_tls = get_smtp_config()
    plain_text = plain_body or html_body
    
    # Check if SMTP is configured
    if not username or not password:
        logger.info(f"[Mock / Log Mode] Email to {to_email} with subject '{subject}' recorded (SMTP not configured).")
        log_entry = EmailLog(
            recipient=to_email,
            subject=subject,
            body=plain_text,
            status="Logged (No SMTP)",
            job_id=job_id,
            application_id=application_id,
            sent_at=datetime.utcnow()
        )
        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to save email log: {e}")
            db.session.rollback()
        return True, "Email recorded to system log (SMTP credentials not configured)."

    # Attempt actual SMTP sending
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        
        part1 = MIMEText(plain_text, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(server, port, timeout=10) as s:
            if use_tls:
                s.starttls()
            s.login(username, password)
            s.sendmail(sender, [to_email], msg.as_string())
            
        logger.info(f"Successfully sent email to {to_email} via SMTP.")
        log_entry = EmailLog(
            recipient=to_email,
            subject=subject,
            body=plain_text,
            status="Sent",
            job_id=job_id,
            application_id=application_id,
            sent_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        return True, "Email sent successfully."
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        log_entry = EmailLog(
            recipient=to_email,
            subject=subject,
            body=plain_text,
            status="Failed",
            error_message=str(e),
            job_id=job_id,
            application_id=application_id,
            sent_at=datetime.utcnow()
        )
        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return False, str(e)

# ---------------------------------------------
# Standard Automated Email Templates
# ---------------------------------------------

def send_application_received_email(application):
    """Triggered immediately when an applicant submits their resume"""
    job = application.job
    subject = f"Application Received: {job.title} — AI-Powered Recruitment Agent"
    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 8px; background-color: #FFFFFF;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #3730A3; margin: 0;">AI-Powered Recruitment Agent</h2>
            <p style="color: #0D9488; font-weight: 600; margin: 4px 0 0 0;">Intelligent Talent Screening Platform</p>
        </div>
        <div style="background-color: #F8FAFC; border-left: 4px solid #0EA5E9; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1E293B;">Hello {application.applicant_name},</h3>
            <p style="color: #475569; line-height: 1.6; margin-bottom: 0;">
                Thank you for applying for the position of <strong>{job.title}</strong> ({job.department}). 
                Our AI screening system has received your resume and is analyzing your skills and qualifications.
            </p>
        </div>
        <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
            <strong>Application Reference:</strong> #{application.id}<br>
            <strong>Date Received:</strong> {application.applied_at.strftime('%B %d, %Y %I:%M %p')}<br>
            <strong>Status:</strong> Under AI Review
        </p>
        <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
            You can log into your applicant portal at any time to review AI resume optimization feedback.
        </p>
        <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 24px 0;">
        <p style="font-size: 12px; color: #94A3B8; text-align: center; margin: 0;">
            AI-Powered Recruitment Agent Screening Engine &bull; Automated Notification
        </p>
    </div>
    """
    return send_email(
        to_email=application.applicant_email,
        subject=subject,
        html_body=html,
        plain_body=f"Hello {application.applicant_name},\n\nYour application for {job.title} has been received. Our team will review your profile shortly.\n\nAI-Powered Recruitment Agent Team",
        job_id=job.id,
        application_id=application.id
    )

def send_status_update_email(application, new_status):
    """Triggered when a recruiter updates applicant status (Shortlisted, On Hold, Rejected)"""
    job = application.job
    subject = f"Application Status Update: {job.title} — AI-Powered Recruitment Agent"
    
    status_lower = new_status.lower()
    if "shortlist" in status_lower:
        badge_color = "#16A34A"
        headline = "Great news! You have been shortlisted."
        message = (
            f"Congratulations! After reviewing your resume for <strong>{job.title}</strong>, "
            f"the recruiting team has marked your application as <strong>Shortlisted</strong>. "
            f"You demonstrated strong alignment with the role's required competencies. "
            f"The hiring team will reach out with interview details soon."
        )
    elif "hold" in status_lower:
        badge_color = "#F59E0B"
        headline = "Your application is currently On Hold."
        message = (
            f"Thank you for your interest in the <strong>{job.title}</strong> role. "
            f"Your application is currently on hold while we evaluate the applicant pool. "
            f"We will provide further updates as the recruitment cycle progresses."
        )
    else:
        badge_color = "#DC2626"
        headline = "Update regarding your application."
        message = (
            f"Thank you for taking the time to apply for <strong>{job.title}</strong>. "
            f"After careful review against our current job criteria, we have decided not to advance your application at this time. "
            f"We encourage you to log into the platform to view tailored AI resume improvement feedback for future opportunities."
        )

    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 8px; background-color: #FFFFFF;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #3730A3; margin: 0;">AI-Powered Recruitment Agent</h2>
            <p style="color: #0D9488; font-weight: 600; margin: 4px 0 0 0;">Intelligent Talent Screening Platform</p>
        </div>
        <div style="border-left: 4px solid {badge_color}; background-color: #F8FAFC; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
            <span style="display: inline-block; background-color: {badge_color}; color: #FFFFFF; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 12px; text-transform: uppercase; margin-bottom: 8px;">
                {new_status}
            </span>
            <h3 style="margin: 8px 0; color: #1E293B;">{headline}</h3>
            <p style="color: #475569; line-height: 1.6; margin: 0;">
                {message}
            </p>
        </div>
        <p style="color: #64748B; font-size: 14px;">
            Candidate: <strong>{application.applicant_name}</strong><br>
            Job Role: <strong>{job.title}</strong>
        </p>
        <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 24px 0;">
        <p style="font-size: 12px; color: #94A3B8; text-align: center; margin: 0;">
            AI-Powered Recruitment Agent &bull; Automated Recruitment Notification
        </p>
    </div>
    """
    return send_email(
        to_email=application.applicant_email,
        subject=subject,
        html_body=html,
        plain_body=f"Hello {application.applicant_name},\n\nYour application status for {job.title} has been updated to: {new_status}.\n\nBest regards,\nRecruitment Team",
        job_id=job.id,
        application_id=application.id
    )

def send_recruiter_daily_summary(recruiter, summary_data):
    """Send daily digest email to recruiter with new applicant statistics"""
    subject = f"Daily Digest: {summary_data['total_new']} New Applications Today — AI-Powered Recruitment Agent"
    
    rows_html = ""
    for item in summary_data.get("job_breakdown", []):
        rows_html += f"""
        <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #E2E8F0; color: #1E293B;">{item['title']}</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #E2E8F0; text-align: center; color: #3730A3; font-weight: 700;">{item['count']}</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #E2E8F0; text-align: center; color: #0D9488; font-weight: 700;">{item['avg_score']}%</td>
        </tr>
        """
        
    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 8px; background-color: #FFFFFF;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #3730A3; margin: 0;">AI-Powered Recruitment Agent</h2>
            <p style="color: #64748B; margin-top: 4px;">Recruiter Daily Digest &bull; {datetime.utcnow().strftime('%A, %B %d, %Y')}</p>
        </div>
        
        <p style="color: #1E293B; font-size: 15px;">
            Hello {recruiter.full_name},<br>
            Here is your daily summary of applicant activity screened by AI-Powered Recruitment Agent.
        </p>
        
        <div style="display: flex; justify-content: space-between; margin: 20px 0; background: #F8FAFC; padding: 16px; border-radius: 8px;">
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 28px; font-weight: 800; color: #3730A3;">{summary_data['total_new']}</div>
                <div style="font-size: 12px; color: #64748B; text-transform: uppercase;">New Applications</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 28px; font-weight: 800; color: #16A34A;">{summary_data['total_shortlisted']}</div>
                <div style="font-size: 12px; color: #64748B; text-transform: uppercase;">High Match Shortlisted</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 28px; font-weight: 800; color: #0D9488;">{summary_data['avg_score']}%</div>
                <div style="font-size: 12px; color: #64748B; text-transform: uppercase;">Avg AI Match Score</div>
            </div>
        </div>
        
        <h4 style="color: #1E293B; margin-bottom: 10px;">Applications Breakdown by Job</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 24px;">
            <thead>
                <tr style="background-color: #3730A3; color: #FFFFFF;">
                    <th style="padding: 10px 14px; text-align: left;">Job Role</th>
                    <th style="padding: 10px 14px; text-align: center;">New Candidates</th>
                    <th style="padding: 10px 14px; text-align: center;">Avg Score</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else "<tr><td colspan='3' style='text-align: center; padding: 15px;'>No new applications submitted today.</td></tr>"}
            </tbody>
        </table>
        
        <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 24px 0;">
        <p style="font-size: 12px; color: #94A3B8; text-align: center; margin: 0;">
            AI-Powered Recruitment Agent &bull; Scheduled Daily Automation
        </p>
    </div>
    """
    return send_email(
        to_email=recruiter.email,
        subject=subject,
        html_body=html,
        plain_body=f"Hello {recruiter.full_name},\n\nYou have {summary_data['total_new']} new applications today. Log in to AI-Powered Recruitment Agent to view candidates.\n\nRecruitment System"
    )
