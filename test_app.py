import unittest
import json
import io
from app import create_app
from app.extensions import db
from app.models import User, JobPost, Application

class SmartHireTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_homepage_redirect(self):
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])

    def test_applicant_jobs_list(self):
        response = self.client.get("/applicant/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Senior Python", response.data)

    def test_recruiter_dashboard_auth_redirect(self):
        # Without login, should redirect to login
        response = self.client.get("/recruiter/dashboard")
        self.assertEqual(response.status_code, 302)

    def test_recruiter_login_and_dashboard(self):
        # Login as recruiter
        login_res = self.client.post("/auth/login", data={
            "email": "recruiter@smarthire.ai",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Recruiter Command Center", login_res.data)

        # View job detail & ranked list
        with self.app.app_context():
            job = JobPost.query.first()
            job_id = job.id

        job_res = self.client.get(f"/recruiter/jobs/{job_id}")
        self.assertEqual(job_res.status_code, 200)
        self.assertIn(b"Ayesha Khan", job_res.data)
        self.assertIn(b"92%", job_res.data)

        # Test CSV export
        csv_res = self.client.get(f"/recruiter/jobs/{job_id}/export/csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn(b"Ayesha Khan", csv_res.data)

        # Test PDF export
        pdf_res = self.client.get(f"/recruiter/jobs/{job_id}/export/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")

        # Test applicant detail review
        with self.app.app_context():
            app_record = Application.query.first()
            app_id = app_record.id

        detail_res = self.client.get(f"/recruiter/applications/{app_id}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b"AI Interview Questions", detail_res.data)
        self.assertIn(b"AI Resume Match Analysis", detail_res.data)

        # Test Email logs
        emails_res = self.client.get("/recruiter/emails")
        self.assertEqual(emails_res.status_code, 200)

        # Test Settings
        settings_res = self.client.get("/recruiter/settings")
        self.assertEqual(settings_res.status_code, 200)

    def test_applicant_flow_and_feedback(self):
        # Login as applicant
        login_res = self.client.post("/auth/login", data={
            "email": "ayesha@example.com",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        dash_res = self.client.get("/applicant/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"My Application Portfolio", dash_res.data)

        with self.app.app_context():
            app_record = Application.query.filter_by(applicant_email="ayesha@example.com").first()
            app_id = app_record.id

        fb_res = self.client.get(f"/applicant/applications/{app_id}/feedback")
        self.assertEqual(fb_res.status_code, 200)
        self.assertIn(b"ATS Compatibility Score", fb_res.data)
        self.assertIn(b"Actionable Resume Optimization Guidance", fb_res.data)

    def test_apply_with_resume_upload(self):
        # Test applying to a job with PDF upload
        with self.app.app_context():
            job = JobPost.query.filter_by(title="Full Stack Web Developer").first()
            job_id = job.id

        sample_pdf_path = "sample_resumes/Ayesha_Khan_Resume.pdf"
        with open(sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        response = self.client.post(
            f"/applicant/jobs/{job_id}/apply",
            data={
                "name": "David Miller",
                "email": "david.miller@example.com",
                "phone": "+1 555-443-1299",
                "resume": (io.BytesIO(pdf_bytes), "David_Miller_Resume.pdf")
            },
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Resume Feedback", response.data)
        self.assertIn(b"David Miller", response.data)

if __name__ == "__main__":
    unittest.main()
