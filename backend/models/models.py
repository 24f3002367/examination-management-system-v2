from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(50), default="")
    department = db.Column(db.String(100), default="")
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(30), unique=True, nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="Active")

class Examination(db.Model):
    __tablename__ = "examinations"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    exam_name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, default=30)
    max_marks = db.Column(db.Float, default=100.0)
    instructions = db.Column(db.Text, default="")
    slot_creation_start = db.Column(db.String(30), nullable=False)
    slot_creation_end = db.Column(db.String(30), nullable=False)
    slot_booking_start = db.Column(db.String(30), nullable=False)
    slot_booking_end = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default="Draft")
    results_published = db.Column(db.Boolean, default=False)

    course = db.relationship("Course", backref="examinations")
    examiner = db.relationship("User", foreign_keys=[examiner_id])

class Rubric(db.Model):
    __tablename__ = "rubrics"
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    criterion_name = db.Column(db.String(120), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, default=100.0)
    description = db.Column(db.Text, default="")

    exam = db.relationship("Examination", backref="rubrics")

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