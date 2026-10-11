"""Customers: the list, adding one, and one customer's page and history."""

from flask import Blueprint, abort, jsonify, render_template, request

from sari_utang.database import get_db
from sari_utang.domain.paging import DEFAULT_PER_PAGE
from sari_utang.services import CustomerService, TransactionService
from sari_utang.web.security import json_body, login_required_api, login_required_page

bp = Blueprint("customers", __name__)


@bp.get("/customers")
@login_required_page
def list_page():
    return render_template("customers.html")


@bp.get("/customers/<int:customer_id>")
@login_required_page
def detail_page(customer_id):
    if not CustomerService(get_db()).exists(customer_id):
        abort(404)
    return render_template("customer.html", customer_id=customer_id)


@bp.get("/api/customers")
@login_required_api
def api_list():
    """?page=2&per_page=20&q=nena : one page of the customers whose name or phone has "nena".
    Without ?page= : all customers."""
    return jsonify(CustomerService(get_db()).list(
        request.args.get("page", type=int),
        request.args.get("per_page", default=DEFAULT_PER_PAGE, type=int),
        request.args.get("q", ""),
    ))


@bp.post("/api/customers")
@login_required_api
def api_create():
    return jsonify(customer=CustomerService(get_db()).create(json_body())), 201


@bp.get("/api/customers/<int:customer_id>/transactions")
@login_required_api
def api_history(customer_id):
    return jsonify(TransactionService(get_db()).history(customer_id))
