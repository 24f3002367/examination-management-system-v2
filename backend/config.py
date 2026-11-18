import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "mad2-exam-portal-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "exam_portal.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "mad2-jwt-secret-key"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    REDIS_URL = "redis://localhost:6379/0"
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    MAIL_HOST = "localhost"
    MAIL_PORT = 1025
    SENDER_EMAIL = "noreply@examportal.edu"