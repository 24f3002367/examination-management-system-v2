from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()
    contact = data.get("contact", "").strip()
    department = data.get("department", "").strip()

    if not username or not email or not password or not full_name:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "User already exists"}), 400

    student = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role="student",
        full_name=full_name,
        contact=contact,
        department=department,
        status="Active"
    )
    db.session.add(student)
    db.session.commit()
    return jsonify({"message": "Student registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = User.query.filter((User.username == username) | (User.email == username)).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    if user.status != "Active":
        return jsonify({"error": "Account is inactive"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "contact": user.contact,
            "department": user.department
        }
    }), 200

@auth_bp.route("/profile", methods=["GET", "PUT"])
@jwt_required()
def profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if request.method == "GET":
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "contact": user.contact,
            "department": user.department
        }), 200

    data = request.get_json() or {}
    user.full_name = data.get("full_name", user.full_name)
    user.email = data.get("email", user.email)
    user.contact = data.get("contact", user.contact)
    user.department = data.get("department", user.department)
    if data.get("password"):
        user.password_hash = generate_password_hash(data["password"])
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"}), 200