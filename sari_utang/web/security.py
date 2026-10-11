"""Who is logged in, and decorators that let only a logged-in person open a page or API."""

from functools import wraps

from flask import jsonify, redirect, request, session, url_for


def is_logged_in():
    return session.get("logged_in") is True


def json_body():
    """The posted JSON object, or {} when there is none."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def login_required_page(view):
    """For HTML pages: send the user to the login page if not logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("auth.login_page"))
        return view(*args, **kwargs)
    return wrapper


def login_required_api(view):
    """For API routes: answer 401 if not logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return jsonify(error="Please log in."), 401
        return view(*args, **kwargs)
    return wrapper
