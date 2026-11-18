import csv
import io
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from config import Config
from services import send_email

celery = Celery("exam_tasks", broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
celery.conf.timezone = "Asia/Kolkata"

celery.conf.beat_schedule = {
    "daily-exam-reminders": {
        "task": "tasks.send_daily_exam_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "monthly-admin-report": {
        "task": "tasks.send_monthly_admin_report",
        "schedule": crontab(day_of_month=1, hour=9, minute=0),
    },
}

@celery.task(name="tasks.send_daily_exam_reminders")
def send_daily_exam_reminders():
    from app import create_app
    from models import Booking
    app = create_app()
    with app.app_context():
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        bookings = Booking.query.filter_by(status="Booked").all()
        sent = 0
        for b in bookings:
            if b.slot.slot_date in (today, tomorrow):
                exam = b.slot.exam
                body = f"""
                <h3>Exam Reminder</h3>
                <p>Hello {b.student.full_name},</p>
                <p>Exam: {exam.exam_name}</p>
                <p>Date: {b.slot.slot_date} ({b.slot.start_time} - {b.slot.end_time})</p>
                """
                send_email(b.student.email, f"Reminder: {exam.exam_name}", body)
                sent += 1
        return f"Sent {sent} reminders"

@celery.task(name="tasks.send_monthly_admin_report")
def send_monthly_admin_report():
    from app import create_app
    from models import User, Examination, Booking, Evaluation
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            return "No admin found"

        total_exams = Examination.query.count()
        total_evaluated = Evaluation.query.count()
        completed_bookings = Booking.query.filter_by(status="Completed").count()

        html = f"""
        <h2>Monthly Admin Report</h2>
        <p>Total Exams: {total_exams}</p>
        <p>Total Evaluated: {total_evaluated}</p>
        <p>Completed Bookings: {completed_bookings}</p>
        """
        send_email(admin.email, "Monthly Exam Report", html)
        return "Report sent"

@celery.task(name="tasks.export_student_history_csv")
def export_student_history_csv(student_id):
    from app import create_app
    from models import Booking, Evaluation
    app = create_app()
    with app.app_context():
        bookings = Booking.query.filter_by(student_id=student_id).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Examination Name", "Course", "Examination Date", "Examiner", "Marks Obtained", "Booking Status"])
        for b in bookings:
            exam = b.slot.exam
            ev = Evaluation.query.filter_by(booking_id=b.id).first()
            marks = ev.total_marks if (ev and exam.results_published) else "N/A"
            writer.writerow([
                student_id,
                exam.exam_name,
                exam.course.course_name if exam.course else "",
                b.slot.slot_date,
                b.slot.examiner.full_name if b.slot.examiner else "",
                marks,
                b.status
            ])
        return output.getvalue()