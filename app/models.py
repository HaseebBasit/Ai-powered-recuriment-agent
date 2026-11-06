import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="applicant")  # recruiter or applicant
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    jobs = db.relationship("JobPost", backref="recruiter", lazy=True, cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="applicant", lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_recruiter(self):
        return self.role == "recruiter"
    
    @property
    def is_applicant(self):
        return self.role == "applicant"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class JobPost(db.Model):
    __tablename__ = "job_posts"
    
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), default="General")
    location = db.Column(db.String(100), default="Remote / Hybrid")
    employment_type = db.Column(db.String(50), default="Full-time")  # Full-time, Part-time, Internship, Contract
    min_experience = db.Column(db.Integer, default=0)  # in years
    required_skills = db.Column(db.Text, nullable=False)  # comma separated or tags
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")  # Open, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    
    applications = db.relationship("Application", backref="job", lazy=True, cascade="all, delete-orphan")
    
    def get_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(",") if s.strip()]

class Application(db.Model):
    __tablename__ = "applications"
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job_posts.id"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    applicant_name = db.Column(db.String(120), nullable=False)
    applicant_email = db.Column(db.String(120), nullable=False)
    applicant_phone = db.Column(db.String(50), nullable=True)
    
    resume_filename = db.Column(db.String(255), nullable=False)
    resume_path = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    
    # AI Parsed & Screening Data
    parsed_data = db.Column(db.Text, nullable=True)  # JSON string
    match_score = db.Column(db.Integer, default=0)   # 0 to 100
    match_justification = db.Column(db.Text, nullable=True)
    matching_skills = db.Column(db.Text, nullable=True)  # JSON string list
    missing_skills = db.Column(db.Text, nullable=True)   # JSON string list
    
    # Status: 'Applied', 'Shortlisted', 'On Hold', 'Rejected'
    status = db.Column(db.String(30), default="Applied")
    
    # AI tailored content
    ai_feedback = db.Column(db.Text, nullable=True)  # Resume improvement tips
    interview_questions = db.Column(db.Text, nullable=True)  # JSON string list
    
    recruiter_notes = db.Column(db.Text, nullable=True)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_parsed_dict(self):
        if not self.parsed_data:
            return {}
        try:
            return json.loads(self.parsed_data)
        except Exception:
            return {}
            
    def get_matching_skills_list(self):
        if not self.matching_skills:
            return []
        try:
            return json.loads(self.matching_skills)
        except Exception:
            return [s.strip() for s in self.matching_skills.split(",") if s.strip()]
            
    def get_missing_skills_list(self):
        if not self.missing_skills:
            return []
        try:
            return json.loads(self.missing_skills)
        except Exception:
            return [s.strip() for s in self.missing_skills.split(",") if s.strip()]
            
    def get_interview_questions_list(self):
        if not self.interview_questions:
            return []
        try:
            return json.loads(self.interview_questions)
        except Exception:
            return [q.strip() for q in self.interview_questions.split("\n") if q.strip()]

    @property
    def score_color_class(self):
        # According to Brand Guide:
        # High match (70-100) -> Shortlisted #16A34A (green)
        # Medium match (40-69) -> On Hold #F59E0B (amber)
        # Low match (0-39) -> Rejected #DC2626 (red)
        if self.match_score >= 70:
            return "success"
        elif self.match_score >= 40:
            return "warning"
        else:
            return "danger"
            
    @property
    def status_badge_class(self):
        # Shortlisted, On Hold, Rejected, Applied
        status_lower = (self.status or "applied").lower()
        if "shortlist" in status_lower:
            return "badge-shortlisted"
        elif "hold" in status_lower:
            return "badge-on-hold"
        elif "reject" in status_lower:
            return "badge-rejected"
        else:
            return "badge-applied"

class EmailLog(db.Model):
    __tablename__ = "email_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Sent")  # Sent, Logged (No SMTP), Failed
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    job_id = db.Column(db.Integer, nullable=True)
    application_id = db.Column(db.Integer, nullable=True)

class SystemConfig(db.Model):
    __tablename__ = "system_configs"
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    
    @staticmethod
    def get_value(key, default=None):
        cfg = SystemConfig.query.get(key)
        if cfg and cfg.value:
            return cfg.value
        return default

    @staticmethod
    def set_value(key, value):
        cfg = SystemConfig.query.get(key)
        if not cfg:
            cfg = SystemConfig(key=key, value=value)
            db.session.add(cfg)
        else:
            cfg.value = value
        db.session.commit()


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_posts.id"), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref=db.backref("saved_jobs", lazy=True))
    job = db.relationship("JobPost", backref=db.backref("saved_by", lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='unique_saved_job'),)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
