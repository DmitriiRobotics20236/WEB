from functools import wraps

from flask import abort
from flask_login import current_user


def for_sellers(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_seller:
            return func(*args, **kwargs)
        else:
            abort(403)
    return wrapper
