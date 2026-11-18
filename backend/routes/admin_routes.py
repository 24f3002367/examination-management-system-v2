from functools import wraps
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Course, Examination, Rubric, ExamSlot, Booking, Evaluation
from services import clear_exam_cache

admin_bp = Blueprint("admin_bp", __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = User.query.get(int(get_jwt_identity()))
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    exams = Examination.query.all()
    exam_labels = [e.exam_name for e in exams]
    booking_counts = []
    for e in exams:
        count = Booking.query.join(ExamSlot).filter(ExamSlot.exam_id == e.id, Booking.status != "Cancelled").count()
        booking_counts.append(count)

    examiners = User.query.filter_by(role="examiner").all()
    examiner_labels = [ex.full_name for ex in examiners]
    examiner_slots = [ExamSlot.query.filter_by(examiner_id=ex.id).count() for ex in examiners]

    return jsonify({
        "total_courses": Course.query.count(),
        "total_exams": Examination.query.count(),
        "total_students": User.query.filter_by(role="student").count(),
        "total_examiners": User.query.filter_by(role="examiner").count(),
        "total_slots": ExamSlot.query.count(),
        "total_bookings": Booking.query.count(),
        "charts": {
            "exam_labels": exam_labels,
            "booking_counts": booking_counts,
            "examiner_labels": examiner_labels,
            "examiner_slots": examiner_slots
        }
    }), 200

@admin_bp.route("/courses", methods=["GET", "POST"])
@admin_required
def courses():
    if request.method == "GET":
        items = Course.query.all()
        return jsonify([{
            "id": c.id,
            "course_code": c.course_code,
            "course_name": c.course_name,
            "description": c.description,
            "status": c.status
        } for c in items]), 200

    data = request.get_json() or {}
    if not data.get("course_code") or not data.get("course_name"):
        return jsonify({"error": "Course code and name required"}), 400
    if Course.query.filter_by(course_code=data["course_code"]).first():
        return jsonify({"error": "Course code exists"}), 400

    course = Course(
        course_code=data["course_code"],
        course_name=data["course_name"],
        description=data.get("description", ""),
        status=data.get("status", "Active")
    )
    db.session.add(course)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Course created", "id": course.id}), 201

@admin_bp.route("/courses/<int:course_id>", methods=["PUT", "DELETE"])
@admin_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "DELETE":
        db.session.delete(course)
        db.session.commit()
        clear_exam_cache()
        return jsonify({"message": "Course deleted"}), 200

    data = request.get_json() or {}
    course.course_code = data.get("course_code", course.course_code)
    course.course_name = data.get("course_name", course.course_name)
    course.description = data.get("description", course.description)
    course.status = data.get("status", course.status)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Course updated"}), 200

@admin_bp.route("/examiners", methods=["GET", "POST"])
@admin_required
def examiners():
    if request.method == "GET":
        items = User.query.filter_by(role="examiner").all()
        return jsonify([{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "contact": u.contact,
            "department": u.department,
            "status": u.status
        } for u in items]), 200

    data = request.get_json() or {}
    if not data.get("username") or not data.get("email") or not data.get("password") or not data.get("full_name"):
        return jsonify({"error": "Missing required fields"}), 400

    examiner = User(
        username=data["username"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        role="examiner",
        full_name=data["full_name"],
        contact=data.get("contact", ""),
        department=data.get("department", ""),
        status="Active"
    )
    db.session.add(examiner)
    db.session.commit()
    return jsonify({"message": "Examiner added", "id": examiner.id}), 201

@admin_bp.route("/examiners/<int:examiner_id>", methods=["DELETE"])
@admin_required
def delete_examiner(examiner_id):
    examiner = User.query.filter_by(id=examiner_id, role="examiner").first_or_404()
    db.session.delete(examiner)
    db.session.commit()
    return jsonify({"message": "Examiner removed"}), 200

@admin_bp.route("/students", methods=["GET"])
@admin_required
def students():
    items = User.query.filter_by(role="student").all()
    return jsonify([{
        "id": s.id,
        "username": s.username,
        "email": s.email,
        "full_name": s.full_name,
        "contact": s.contact,
        "department": s.department,
        "status": s.status
    } for s in items]), 200

@admin_bp.route("/exams", methods=["GET", "POST"])
@admin_required
def exams():
    if request.method == "GET":
        items = Examination.query.all()
        return jsonify([{
            "id": e.id,
            "course_id": e.course_id,
            "course_name": e.course.course_name if e.course else "",
            "examiner_id": e.examiner_id,
            "examiner_name": e.examiner.full_name if e.examiner else "Unassigned",
            "exam_name": e.exam_name,
            "exam_type": e.exam_type,
            "duration": e.duration,
            "max_marks": e.max_marks,
            "instructions": e.instructions,
            "slot_creation_start": e.slot_creation_start,
            "slot_creation_end": e.slot_creation_end,
            "slot_booking_start": e.slot_booking_start,
            "slot_booking_end": e.slot_booking_end,
            "status": e.status,
            "results_published": e.results_published
        } for e in items]), 200

    data = request.get_json() or {}
    exam = Examination(
        course_id=data["course_id"],
        examiner_id=data.get("examiner_id") or None,
        exam_name=data["exam_name"],
        exam_type=data["exam_type"],
        duration=int(data.get("duration", 30)),
        max_marks=float(data.get("max_marks", 100)),
        instructions=data.get("instructions", ""),
        slot_creation_start=data["slot_creation_start"],
        slot_creation_end=data["slot_creation_end"],
        slot_booking_start=data["slot_booking_start"],
        slot_booking_end=data["slot_booking_end"],
        status=data.get("status", "Draft")
    )
    db.session.add(exam)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Examination created", "id": exam.id}), 201

@admin_bp.route("/exams/<int:exam_id>", methods=["PUT", "DELETE"])
@admin_required
def exam_detail(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    if request.method == "DELETE":
        db.session.delete(exam)
        db.session.commit()
        clear_exam_cache()
        return jsonify({"message": "Examination deleted"}), 200

    data = request.get_json() or {}
    exam.course_id = data.get("course_id", exam.course_id)
    exam.examiner_id = data.get("examiner_id", exam.examiner_id)
    exam.exam_name = data.get("exam_name", exam.exam_name)
    exam.exam_type = data.get("exam_type", exam.exam_type)
    exam.duration = int(data.get("duration", exam.duration))
    exam.max_marks = float(data.get("max_marks", exam.max_marks))
    exam.instructions = data.get("instructions", exam.instructions)
    exam.slot_creation_start = data.get("slot_creation_start", exam.slot_creation_start)
    exam.slot_creation_end = data.get("slot_creation_end", exam.slot_creation_end)
    exam.slot_booking_start = data.get("slot_booking_start", exam.slot_booking_start)
    exam.slot_booking_end = data.get("slot_booking_end", exam.slot_booking_end)
    exam.status = data.get("status", exam.status)
    if "results_published" in data:
        exam.results_published = bool(data["results_published"])
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Examination updated"}), 200

@admin_bp.route("/rubrics", methods=["GET", "POST"])
@admin_required
def rubrics():
    if request.method == "GET":
        exam_id = request.args.get("exam_id")
        query = Rubric.query
        if exam_id:
            query = query.filter_by(exam_id=int(exam_id))
        items = query.all()
        return jsonify([{
            "id": r.id,
            "exam_id": r.exam_id,
            "exam_name": r.exam.exam_name if r.exam else "",
            "criterion_name": r.criterion_name,
            "max_marks": r.max_marks,
            "weightage": r.weightage,
            "description": r.description
        } for r in items]), 200

    data = request.get_json() or {}
    rubric = Rubric(
        exam_id=int(data["exam_id"]),
        criterion_name=data["criterion_name"],
        max_marks=float(data["max_marks"]),
        weightage=float(data.get("weightage", 100)),
        description=data.get("description", "")
    )
    db.session.add(rubric)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Rubric added", "id": rubric.id}), 201

@admin_bp.route("/rubrics/<int:rubric_id>", methods=["DELETE"])
@admin_required
def delete_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    db.session.delete(rubric)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Rubric deleted"}), 200

@admin_bp.route("/slots", methods=["GET"])
@admin_required
def all_slots():
    slots = ExamSlot.query.all()
    return jsonify([{
        "id": s.id,
        "exam_id": s.exam_id,
        "exam_name": s.exam.exam_name if s.exam else "",
        "examiner_id": s.examiner_id,
        "examiner_name": s.examiner.full_name if s.examiner else "",
        "slot_date": s.slot_date,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "max_capacity": s.max_capacity,
        "available_seats": s.available_seats,
        "status": s.status,
        "meeting_link": s.meeting_link
    } for s in slots]), 200

@admin_bp.route("/slots/<int:slot_id>/reassign", methods=["PUT"])
@admin_required
def reassign_slot_examiner(slot_id):
    slot = ExamSlot.query.get_or_404(slot_id)
    data = request.get_json() or {}
    slot.examiner_id = int(data["examiner_id"])
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Examiner reassigned successfully"}), 200

@admin_bp.route("/bookings", methods=["GET"])
@admin_required
def all_bookings():
    bookings = Booking.query.all()
    return jsonify([{
        "id": b.id,
        "student_id": b.student_id,
        "student_name": b.student.full_name if b.student else "",
        "slot_id": b.slot_id,
        "exam_id": b.slot.exam_id if b.slot else None,
        "exam_name": b.slot.exam.exam_name if b.slot and b.slot.exam else "",
        "examiner_name": b.slot.examiner.full_name if b.slot and b.slot.examiner else "",
        "slot_date": b.slot.slot_date if b.slot else "",
        "start_time": b.slot.start_time if b.slot else "",
        "end_time": b.slot.end_time if b.slot else "",
        "status": b.status
    } for b in bookings]), 200

@admin_bp.route("/bookings/<int:booking_id>/reschedule", methods=["PUT"])
@admin_required
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json() or {}
    new_slot = ExamSlot.query.get_or_404(int(data["new_slot_id"]))

    if new_slot.available_seats <= 0:
        return jsonify({"error": "Target slot is full"}), 400

    old_slot = booking.slot
    if old_slot:
        old_slot.available_seats += 1
        if old_slot.status == "Full":
            old_slot.status = "Available"

    new_slot.available_seats -= 1
    if new_slot.available_seats == 0:
        new_slot.status = "Full"

    booking.slot_id = new_slot.id
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Booking rescheduled successfully"}), 200