from datetime import datetime
from .db import db

class ExamSlot(db.Model):
    __tablename__ = "exam_slots"
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    max_capacity = db.Column(db.Integer, default=1)
    available_seats = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="Available")
    meeting_link = db.Column(db.String(255), default="")

    exam = db.relationship("Examination", backref="slots")
    examiner = db.relationship("User", foreign_keys=[examiner_id])

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("exam_slots.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Booked")

    student = db.relationship("User", foreign_keys=[student_id])
    slot = db.relationship("ExamSlot", backref="bookings")

class Evaluation(db.Model):
    __tablename__ = "evaluations"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rubric_scores = db.Column(db.Text, default="{}")
    total_marks = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text, default="")
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Completed")

    booking = db.relationship("Booking", backref="evaluation")
    student = db.relationship("User", foreign_keys=[student_id])
    examiner = db.relationship("User", foreign_keys=[examiner_id])