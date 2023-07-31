from datetime import datetime, timezone


fake_time = None


def set_fake_time(dt):
    global fake_time
    fake_time = dt


def now():
    if fake_time:
        return fake_time
    return datetime.now(timezone.utc).replace(microsecond=0)
