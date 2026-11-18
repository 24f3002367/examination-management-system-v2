from .db import db

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