"""Login page, login and logout."""

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from sari_utang.database import get_db
from sari_utang.services import AuthService
from sari_utang.web.security import is_logged_in, json_body

bp = Blueprint("auth", __name__)


@bp.get("/")
def index():
    return redirect(url_for("dashboard.page" if is_logged_in() else "auth.login_page"))


@bp.get("/login")
def login_page():
    if is_logged_in():
        return redirect(url_for("dashboard.page"))
    return render_template("login.html")


@bp.post("/api/login")
def api_login():
    throttle = current_app.extensions["login_throttle"]
    AuthService(get_db()).login(json_body().get("pin", ""), request.remote_addr, throttle)
    session.clear()
    session.permanent = True
    session["logged_in"] = True
    return jsonify(ok=True)


@bp.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)
