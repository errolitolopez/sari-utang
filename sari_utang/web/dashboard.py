"""Dashboard: total utang, biggest balances, recent transactions."""

from flask import Blueprint, jsonify, render_template

from sari_utang.database import get_db
from sari_utang.services import CollectionService
from sari_utang.web.security import login_required_api, login_required_page

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required_page
def page():
    return render_template("dashboard.html")


@bp.get("/api/dashboard")
@login_required_api
def api_summary():
    return jsonify(CollectionService(get_db()).dashboard())
