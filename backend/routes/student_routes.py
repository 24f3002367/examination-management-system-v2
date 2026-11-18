import json
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Examination, ExamSlot, Booking, Evaluation
from services import clear_exam_cache

student_bp = Blueprint("student_bp", __name__)

def student_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = User.query.get(int(get_jwt_identity()))
        if not user or user.role != "student":
            return jsonify({"error": "Student access required"}), 403
        return fn(user, *args, **kwargs)
    return wrapper

@student_bp.route("/exams", methods=["GET"])
@student_required
def available_exams(user):
    r = current_app.config.get("REDIS_CLIENT")
    cache_key = "exam_student_list"
    if r:
        cached = r.get(cache_key)
        if cached:
            return jsonify(json.loads(cached)), 200

    exams = Examination.query.filter(Examination.status != "Draft").all()
    data = [{
        "id": e.id,
        "course_code": e.course.course_code if e.course else "",
        "course_name": e.course.course_name if e.course else "",
        "exam_name": e.exam_name,
        "exam_type": e.exam_type,
        "duration": e.duration,
        "max_marks": e.max_marks,
        "instructions": e.instructions,
        "slot_booking_start": e.slot_booking_start,
        "slot_booking_end": e.slot_booking_end,
        "status": e.status
    } for e in exams]

    if r:
        r.setex(cache_key, 120, json.dumps(data))
    return jsonify(data), 200

@student_bp.route("/exams/<int:exam_id>/slots", methods=["GET"])
@student_required
def exam_slots(user, exam_id):
    r = current_app.config.get("REDIS_CLIENT")
    cache_key = f"exam_slots_{exam_id}"
    if r:
        cached = r.get(cache_key)
        if cached:
            return jsonify(json.loads(cached)), 200

    slots = ExamSlot.query.filter_by(exam_id=exam_id).all()
    data = [{
        "id": s.id,
        "exam_id": s.exam_id,
        "examiner_name": s.examiner.full_name if s.examiner else "",
        "slot_date": s.slot_date,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "max_capacity": s.max_capacity,
        "available_seats": s.available_seats,
        "status": s.status,
        "meeting_link": s.meeting_link
    } for s in slots]

    if r:
        r.setex(cache_key, 60, json.dumps(data))
    return jsonify(data), 200

@student_bp.route("/book", methods=["POST"])
@student_required
def book_slot(user):
    data = request.get_json() or {}
    slot_id = int(data["slot_id"])
    slot = ExamSlot.query.get_or_404(slot_id)
    exam = slot.exam
    today = datetime.now().strftime("%Y-%m-%d")

    if exam.status != "Booking Open":
        return jsonify({"error": "Booking is not open for this examination"}), 400

    if not (exam.slot_booking_start <= today <= exam.slot_booking_end):
        return jsonify({"error": "Current date is outside the booking window"}), 400

    if slot.available_seats <= 0 or slot.status == "Full":
        return jsonify({"error": "Slot is full"}), 400

    existing = Booking.query.join(ExamSlot).filter(
        Booking.student_id == user.id,
        ExamSlot.exam_id == exam.id,
        Booking.status != "Cancelled"
    ).first()
    if existing:
        return jsonify({"error": "Already booked for this exam"}), 400

    booking = Booking(student_id=user.id, slot_id=slot.id, status="Booked")
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = "Full"

    db.session.add(booking)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Slot booked successfully", "booking_id": booking.id}), 201

@student_bp.route("/bookings", methods=["GET"])
@student_required
def my_bookings(user):
    bookings = Booking.query.filter_by(student_id=user.id).order_by(Booking.booking_date.desc()).all()
    output = []
    for b in bookings:
        slot = b.slot
        exam = slot.exam
        ev = Evaluation.query.filter_by(booking_id=b.id).first()
        published = exam.results_published if exam else False
        output.append({
            "id": b.id,
            "exam_id": exam.id,
            "exam_name": exam.exam_name,
            "course_name": exam.course.course_name if exam.course else "",
            "examiner_name": slot.examiner.full_name if slot.examiner else "",
            "slot_date": slot.slot_date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "meeting_link": slot.meeting_link,
            "status": b.status,
            "exam_status": exam.status,
            "slot_booking_end": exam.slot_booking_end,
            "results_published": published,
            "total_marks": ev.total_marks if (ev and published) else None,
            "max_marks": exam.max_marks,
            "remarks": ev.remarks if (ev and published) else ""
        })
    return jsonify(output), 200

@student_bp.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
@student_required
def cancel_booking(user, booking_id):
    booking = Booking.query.filter_by(id=booking_id, student_id=user.id).first_or_404()
    if booking.status != "Booked":
        return jsonify({"error": "Invalid booking status"}), 400

    exam = booking.slot.exam
    today = datetime.now().strftime("%Y-%m-%d")
    if exam.status != "Booking Open" or today > exam.slot_booking_end:
        return jsonify({"error": "Cancellation is no longer permitted"}), 400

    booking.status = "Cancelled"
    slot = booking.slot
    slot.available_seats += 1
    if slot.status == "Full":
        slot.status = "Available"

    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Booking cancelled"}), 200

@student_bp.route("/export-csv", methods=["POST"])
@student_required
def trigger_csv_export(user):
    from tasks import export_student_history_csv
    task = export_student_history_csv.delay(user.id)
    return jsonify({"message": "Export started", "task_id": task.id}), 202

@student_bp.route("/export-status/<task_id>", methods=["GET"])
@student_required
def check_export_status(user, task_id):
    from tasks import celery
    res = celery.AsyncResult(task_id)
    if res.ready():
        return jsonify({"status": "completed", "csv_data": res.result}), 200
    return jsonify({"status": "pending"}), 200