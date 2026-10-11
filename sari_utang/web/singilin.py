"""Singilin: the customers to collect from."""

from flask import Blueprint, jsonify, render_template

from sari_utang.database import get_db
from sari_utang.services import CollectionService
from sari_utang.web.security import login_required_api, login_required_page

bp = Blueprint("singilin", __name__)


@bp.get("/singilin")
@login_required_page
def page():
    return render_template("singilin.html")


# Not called /api/collect on purpose: ad/tracker blockers block URLs with "collect"
# (analytics tools use it), which made the page fail with "Cannot reach the server".
@bp.get("/api/singilin")
@login_required_api
def api_list():
    return jsonify(CollectionService(get_db()).singilin())
