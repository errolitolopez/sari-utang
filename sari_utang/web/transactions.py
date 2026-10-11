"""Add a credit or a payment, and void one."""

from flask import Blueprint, jsonify

from sari_utang.database import get_db
from sari_utang.services import TransactionService
from sari_utang.web.security import json_body, login_required_api

bp = Blueprint("transactions", __name__)


@bp.post("/api/transactions")
@login_required_api
def api_add():
    return jsonify(TransactionService(get_db()).add(json_body())), 201


@bp.post("/api/transactions/<int:transaction_id>/void")
@login_required_api
def api_void(transaction_id):
    return jsonify(TransactionService(get_db()).void(transaction_id, json_body()))
