"""sari-utang: pautang list for a sari-sari store.

Run with: flask --app app run --debug
"""

import os
import secrets
import time
from datetime import timedelta
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import db

app = Flask(__name__, instance_relative_config=True)

# The instance/ folder holds private files (database, secret key). It is not committed to git.
os.makedirs(app.instance_path, exist_ok=True)
app.config["DATABASE"] = os.path.join(app.instance_path, "sari_utang.db")

# Stay logged in for 30 days so the PIN isn't asked every time.
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def load_secret_key():
    """The secret key signs the login cookie. Create one the first time and reuse it after."""
    path = os.path.join(app.instance_path, "secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app.secret_key = load_secret_key()
db.init_app(app)


# --- Login protection --------------------------------------------------------

# After too many wrong PINs, block that device for a while so the PIN can't be guessed.
MAX_ATTEMPTS = 5
LOCK_SECONDS = 5 * 60
failed_logins = {}  # ip address -> {"count": wrong tries, "locked_until": timestamp}


def is_logged_in():
    return session.get("logged_in") is True


def login_required_page(view):
    """For HTML pages: send the user to the login page if not logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login_page"))
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


# --- Pages -------------------------------------------------------------------

@app.get("/")
def index():
    return redirect(url_for("dashboard_page" if is_logged_in() else "login_page"))


@app.get("/login")
def login_page():
    if is_logged_in():
        return redirect(url_for("dashboard_page"))
    return render_template("login.html")


@app.get("/dashboard")
@login_required_page
def dashboard_page():
    return render_template("dashboard.html")


# --- API ---------------------------------------------------------------------

@app.post("/api/login")
def api_login():
    ip = request.remote_addr
    record = failed_logins.get(ip, {"count": 0, "locked_until": 0})

    wait = int(record["locked_until"] - time.time())
    if wait > 0:
        return jsonify(error=f"Too many wrong PINs. Try again in {wait // 60 + 1} min."), 429

    pin_hash = db.get_setting("pin_hash")
    if pin_hash is None:
        return jsonify(error="No PIN set yet. Run: flask --app app set-pin"), 503

    pin = str((request.get_json(silent=True) or {}).get("pin", ""))
    if not check_password_hash(pin_hash, pin):
        record["count"] += 1
        if record["count"] >= MAX_ATTEMPTS:
            record = {"count": 0, "locked_until": time.time() + LOCK_SECONDS}
        failed_logins[ip] = record
        return jsonify(error="Wrong PIN."), 401

    failed_logins.pop(ip, None)
    session.clear()
    session.permanent = True
    session["logged_in"] = True
    return jsonify(ok=True)


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/dashboard")
@login_required_api
def api_dashboard():
    conn = db.get_db()

    # Balance per customer = total utang - total payments. All amounts are in centavos.
    balances = conn.execute(
        """
        SELECT c.id, c.name,
               COALESCE(SUM(CASE WHEN t.type = 'utang' THEN t.amount ELSE -t.amount END), 0)
                   AS balance
        FROM customers c
        LEFT JOIN transactions t ON t.customer_id = c.id
        GROUP BY c.id
        ORDER BY balance DESC
        """
    ).fetchall()
    with_utang = [row for row in balances if row["balance"] > 0]

    recent = conn.execute(
        """
        SELECT t.id, t.type, t.amount, t.note, t.date, c.name AS customer_name
        FROM transactions t
        JOIN customers c ON c.id = t.customer_id
        ORDER BY t.date DESC, t.id DESC
        LIMIT 5
        """
    ).fetchall()

    return jsonify(
        total_outstanding=sum(row["balance"] for row in with_utang),
        customer_count=len(balances),
        customers_with_utang=len(with_utang),
        top_balances=[dict(row) for row in with_utang[:5]],
        recent_transactions=[dict(row) for row in recent],
    )
