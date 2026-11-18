import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from config import Config
from models import db, User
from routes import auth_bp, admin_bp, examiner_bp, student_bp
from services import get_redis_client

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    app.config["REDIS_CLIENT"] = get_redis_client()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(examiner_bp, url_prefix="/api/examiner")
    app.register_blueprint(student_bp, url_prefix="/api/student")

    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(
                username="admin",
                email="admin@examportal.edu",
                password_hash=generate_password_hash("admin123"),
                role="admin",
                full_name="System Administrator",
                contact="9999999999",
                department="Administration",
                status="Active"
            )
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)