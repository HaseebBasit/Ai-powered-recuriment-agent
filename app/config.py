import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "smarthire-super-secret-key-hackathon-2026")
    
    # SQLite Database (Specification requirement: one SQLite database)
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "smarthire.db"
    
    # Ensure valid SQLAlchemy database URI (SQLite default)
    env_db = os.getenv("DATABASE_URL", "")
    if env_db and (env_db.startswith("sqlite") or env_db.startswith("postgresql") or env_db.startswith("mysql")):
        SQLALCHEMY_DATABASE_URI = env_db
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads" / "resumes"
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # AI APIs
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # Email SMTP (Gmail)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "t")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "SmartHire <noreply@smarthire.ai>")
    
    # Scheduler
    DAILY_SUMMARY_HOUR = int(os.getenv("DAILY_SUMMARY_HOUR", "18"))
    DAILY_SUMMARY_MINUTE = int(os.getenv("DAILY_SUMMARY_MINUTE", "0"))

