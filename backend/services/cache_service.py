import redis
from flask import current_app

def get_redis_client():
    try:
        r = redis.Redis.from_url(current_app.config["REDIS_URL"], decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

def clear_exam_cache():
    r = get_redis_client()
    if r:
        for key in r.scan_iter("exam_*"):
            r.delete(key)