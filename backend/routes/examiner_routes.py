import json
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Examination, Rubric, ExamSlot, Booking, Evaluation
from services import clear_exam_cache

examiner_bp = Blueprint("examiner_bp", __name__)

def examiner_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = User.query.get(int(get_jwt_identity()))
        if not user or user.role != "examiner":
            return jsonify({"error": "Examiner access required"}), 403
        return fn(user, *args, **kwargs)
    return wrapper

def is_slot_finished(slot):
    end_str = f"{slot.slot_date} {slot.end_time[:5]}"
    slot_end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
    return datetime.now() >= slot_end_dt

@examiner_bp.route("/dashboard", methods=["GET"])
@examiner_required
def dashboard(user):
    assigned_exams = Examination.query.filter((Examination.examiner_id == user.id) | (Examination.examiner_id.is_(None))).all()
    my_slots = ExamSlot.query.filter_by(examiner_id=user.id).all()
    slot_ids = [s.id for s in my_slots]
    bookings = Booking.query.filter(Booking.slot_id.in_(slot_ids), Booking.status == "Booked").all() if slot_ids else []
    evaluated_ids = {ev.booking_id for ev in Evaluation.query.filter_by(examiner_id=user.id).all()}
    pending = [b for b in bookings if b.id not in evaluated_ids]

    return jsonify({
        "assigned_exams_count": len(assigned_exams),
        "created_slots_count": len(my_slots),
        "booked_students_count": len(bookings),
        "pending_evaluations_count": len(pending)
    }), 200

@examiner_bp.route("/exams", methods=["GET"])
@examiner_required
def get_assigned_exams(user):
    exams = Examination.query.filter((Examination.examiner_id == user.id) | (Examination.examiner_id.is_(None))).all()
    return jsonify([{
        "id": e.id,
        "course_name": e.course.course_name if e.course else "",
        "exam_name": e.exam_name,
        "exam_type": e.exam_type,
        "duration": e.duration,
        "max_marks": e.max_marks,
        "slot_creation_start": e.slot_creation_start,
        "slot_creation_end": e.slot_creation_end,
        "slot_booking_start": e.slot_booking_start,
        "slot_booking_end": e.slot_booking_end,
        "status": e.status
    } for e in exams]), 200

@examiner_bp.route("/exams/<int:exam_id>/complete", methods=["PUT"])
@examiner_required
def complete_exam(user, exam_id):
    exam = Examination.query.get_or_404(exam_id)
    exam.status = "Completed"
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Examination marked as completed"}), 200

@examiner_bp.route("/slots", methods=["GET", "POST"])
@examiner_required
def manage_slots(user):
    if request.method == "GET":
        slots = ExamSlot.query.filter_by(examiner_id=user.id).all()
        return jsonify([{
            "id": s.id,
            "exam_id": s.exam_id,
            "exam_name": s.exam.exam_name if s.exam else "",
            "slot_date": s.slot_date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "max_capacity": s.max_capacity,
            "available_seats": s.available_seats,
            "status": s.status,
            "meeting_link": s.meeting_link
        } for s in slots]), 200

    data = request.get_json() or {}
    exam = Examination.query.get_or_404(int(data["exam_id"]))
    today = datetime.now().strftime("%Y-%m-%d")

    if exam.status != "Slot Creation":
        return jsonify({"error": "Slot creation is currently closed for this exam"}), 400

    if not (exam.slot_creation_start <= today <= exam.slot_creation_end):
        return jsonify({"error": "Current date is outside the slot creation window"}), 400

    capacity = int(data.get("max_capacity", 1))
    slot = ExamSlot(
        exam_id=exam.id,
        examiner_id=user.id,
        slot_date=data["slot_date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        max_capacity=capacity,
        available_seats=capacity,
        status="Available",
        meeting_link=data.get("meeting_link", "")
    )
    db.session.add(slot)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Slot created", "id": slot.id}), 201

@examiner_bp.route("/slots/<int:slot_id>", methods=["DELETE"])
@examiner_required
def delete_slot(user, slot_id):
    slot = ExamSlot.query.filter_by(id=slot_id, examiner_id=user.id).first_or_404()
    if slot.exam.status != "Slot Creation" or slot.available_seats < slot.max_capacity:
        return jsonify({"error": "Cannot delete slot after slot creation ends or once booked"}), 400
    db.session.delete(slot)
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Slot removed"}), 200

@examiner_bp.route("/evaluate/search", methods=["POST"])
@examiner_required
def search_student_evaluation(user):
    data = request.get_json() or {}
    query_str = data.get("student_query", "").strip().lower()
    exam_id = data.get("exam_id")

    if not query_str or not exam_id:
        return jsonify({"status": "error", "message": "Please provide student name/ID and select an examination."}), 400

    student = User.query.filter(
        User.role == "student",
        ((User.id.ilike(f"%{query_str}%")) | (User.username.ilike(f"%{query_str}%")) | (User.full_name.ilike(f"%{query_str}%")))
    ).first()

    if not student:
        return jsonify({"status": "not_booked", "message": "Student didn't book for this exam."}), 200

    booking = Booking.query.join(ExamSlot).filter(
        Booking.student_id == student.id,
        ExamSlot.exam_id == int(exam_id),
        Booking.status != "Cancelled"
    ).first()

    if not booking:
        return jsonify({"status": "not_booked", "message": "Student didn't book for this exam."}), 200

    slot = booking.slot
    exam = slot.exam

    if not is_slot_finished(slot) and exam.status != "Completed":
        return jsonify({"status": "not_appeared", "message": "Student didn't appear for exam (slot time has not concluded)."}), 200

    ev = Evaluation.query.filter_by(booking_id=booking.id).first()
    rubrics = Rubric.query.filter_by(exam_id=exam.id).all()

    return jsonify({
        "status": "ready",
        "booking_id": booking.id,
        "student_id": student.id,
        "student_name": student.full_name,
        "exam_id": exam.id,
        "exam_name": exam.exam_name,
        "slot_info": f"{slot.slot_date} ({slot.start_time} - {slot.end_time})",
        "existing_marks": ev.total_marks if ev else None,
        "existing_remarks": ev.remarks if ev else "",
        "rubrics": [{
            "id": r.id,
            "criterion_name": r.criterion_name,
            "max_marks": r.max_marks,
            "weightage": r.weightage,
            "description": r.description
        } for r in rubrics]
    }), 200

@examiner_bp.route("/evaluate", methods=["POST"])
@examiner_required
def evaluate_student(user):
    data = request.get_json() or {}
    booking_id = int(data["booking_id"])
    booking = Booking.query.get_or_404(booking_id)

    if booking.slot.examiner_id != user.id:
        return jsonify({"error": "Unauthorized"}), 403

    if not is_slot_finished(booking.slot) and booking.slot.exam.status != "Completed":
        return jsonify({"error": "Evaluation is only permitted after the exam slot date and end time have passed"}), 400

    rubric_scores = data.get("rubric_scores", {})
    total_marks = float(data.get("total_marks", 0))
    remarks = data.get("remarks", "")

    ev = Evaluation.query.filter_by(booking_id=booking.id).first()
    if ev:
        ev.rubric_scores = json.dumps(rubric_scores)
        ev.total_marks = total_marks
        ev.remarks = remarks
        ev.evaluation_date = datetime.utcnow()
    else:
        ev = Evaluation(
            booking_id=booking.id,
            student_id=booking.student_id,
            examiner_id=user.id,
            rubric_scores=json.dumps(rubric_scores),
            total_marks=total_marks,
            remarks=remarks,
            status="Completed"
        )
        db.session.add(ev)

    booking.status = "Completed"
    booking.slot.status = "Completed"
    db.session.commit()
    clear_exam_cache()
    return jsonify({"message": "Evaluation submitted successfully"}), 200