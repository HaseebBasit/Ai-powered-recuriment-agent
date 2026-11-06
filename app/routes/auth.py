from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_recruiter:
            return redirect(url_for("recruiter.dashboard"))
        return redirect(url_for("applicant.dashboard"))
        
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name}!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            if user.is_recruiter:
                return redirect(url_for("recruiter.dashboard"))
            return redirect(url_for("applicant.dashboard"))
        else:
            flash("Invalid email or password. Please verify your credentials.", "danger")
            
    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("recruiter.dashboard" if current_user.is_recruiter else "applicant.dashboard"))
        
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "applicant").strip().lower()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "warning")
            return render_template("auth/register.html")
            
        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "danger")
            return render_template("auth/register.html")
            
        user = User(
            email=email,
            full_name=full_name,
            role=role if role in ["recruiter", "applicant"] else "applicant",
            phone=phone,
            company=company if role == "recruiter" else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f"Account created successfully! Welcome to AI-Powered Recruitment Agent, {user.full_name}.", "success")
        if user.is_recruiter:
            return redirect(url_for("recruiter.dashboard"))
        return redirect(url_for("applicant.dashboard"))
        
    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("auth.login"))
