import os
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from app.config import Config
from app.extensions import db, login_manager, scheduler
from app.services.scheduler_service import init_scheduler

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.recruiter import recruiter_bp
    from app.routes.applicant import applicant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(recruiter_bp)
    app.register_blueprint(applicant_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    # Initialize background scheduler within app context
    with app.app_context():
        db.create_all()
        try:
            init_scheduler(app)
        except Exception as e:
            app.logger.warning(f"Could not start background scheduler: {e}")

    return app
