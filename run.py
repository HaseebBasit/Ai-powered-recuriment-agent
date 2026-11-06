import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    
    print("\n" + "=" * 60)
    print("   SmartHire: AI-Powered Resume Screening & Interview Prep")
    print("=" * 60)
    print(f" * Server running on: http://127.0.0.1:{port}")
    print(" * Recruiter Login:  recruiter@smarthire.ai / password123")
    print(" * Applicant Login:  ayesha@example.com / password123")
    print("=" * 60 + "\n")
    
    app.run(host="127.0.0.1", port=port, debug=debug)

