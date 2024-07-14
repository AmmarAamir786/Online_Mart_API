from uuid import uuid4

def short_uuid():
    return uuid4().hex[:12] 