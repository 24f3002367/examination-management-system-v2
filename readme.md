# Examination Management Portal

A full-stack Examination Management Portal developed for the IITM BS Degree MAD-2 project. The application streamlines exam scheduling, slot creation, student slot bookings, rubric-based evaluations, and result publication across three role-based dashboards (Admin, Examiner, and Student).

## Tech Stack

* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS
* **Frontend:** Vue 3 (ES Modules), Bootstrap 5, Chart.js
* **Database & Caching:** SQLite, Redis (Memurai)
* **Asynchronous Tasks & Scheduling:** Celery, Celery Beat

## Project Structure

```text
MAD2 - EXAM/
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── exam.py
│   │   └── booking.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── admin_routes.py
│   │   ├── examiner_routes.py
│   │   └── student_routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py
│   │   └── email_service.py
│   ├── app.py
│   ├── config.py
│   ├── tasks.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── src/
│       ├── app.js
│       └── components/
│           ├── auth_component.js
│           ├── admin_component.js
│           ├── examiner_component.js
│           └── student_component.js
├── .gitignore
└── README.md


Key Features
Role-Based Access Control (RBAC): Single-entry login routing users automatically to Admin, Examiner, or Student portals via JWT authentication.

Admin Dashboard: Manage courses, examinations, rubrics, examiners, slot reassignments, booking rescheduling, result publication toggles, and visual analytics charts.

Examiner Portal: Create and manage exam time slots during active creation windows, and evaluate students via a targeted lookup bar (validating booking status and exam slot completion time before unlocking rubrics).

Student Portal: Browse exams, book or cancel slots strictly within open booking windows, view published scores and feedback, and export exam history as CSV via background Celery jobs.

Automated Background Jobs: Daily exam reminders and monthly admin reports powered by Celery Beat and Redis.

Setup & Local Execution
1. Prerequisites
Python 3.9+

Redis / Memurai running locally on localhost:6379

2. Environment & Dependencies Setup
Navigate to the backend folder, create a virtual environment, activate it, and install the required packages:

PowerShell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
3. Running the Application
Open 4 separate terminal tabs in the backend directory (with venv activated) and run each service:

Redis Server:

PowerShell
memurai-cli ping
(Ensure Redis/Memurai service is active and responds with PONG)

Celery Worker:

PowerShell
celery -A tasks.celery worker --pool=solo --loglevel=info
Celery Beat:

PowerShell
celery -A tasks.celery beat --loglevel=info
Flask Server:

PowerShell
python app.py
4. Accessing the Application
Open your browser and navigate to: http://127.0.0.1:5000

Default Admin Credentials:

Username: admin

Password: admin123