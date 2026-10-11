"""Products: the list, add, edit, and Excel import/export."""

import io
from datetime import date

from flask import Blueprint, jsonify, render_template, request, send_file

from sari_utang.database import get_db
from sari_utang.domain.paging import DEFAULT_PER_PAGE
from sari_utang.services import ProductExcelService, ProductService
from sari_utang.web.security import json_body, login_required_api, login_required_page

bp = Blueprint("products", __name__)

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@bp.get("/products")
@login_required_page
def page():
    return render_template("products.html", units=ProductService(get_db()).units())


@bp.get("/products/export.xlsx")
@login_required_page
def export():
    """All products as an Excel file: name, price (in pesos), unit."""
    data = ProductExcelService(get_db()).export()
    return send_file(
        io.BytesIO(data), as_attachment=True, mimetype=XLSX_TYPE,
        download_name=f"products-{date.today().isoformat()}.xlsx",
    )


@bp.get("/api/products")
@login_required_api
def api_list():
    """?page=2&per_page=20&q=coke : one page of the products whose name has "coke".
    Without ?page= : all products (the utang form searches all of them)."""
    return jsonify(ProductService(get_db()).list(
        request.args.get("page", type=int),
        request.args.get("per_page", default=DEFAULT_PER_PAGE, type=int),
        request.args.get("q", ""),
    ))


@bp.post("/api/products")
@login_required_api
def api_create():
    return jsonify(product=ProductService(get_db()).create(json_body())), 201


@bp.put("/api/products/<int:product_id>")
@login_required_api
def api_update(product_id):
    return jsonify(product=ProductService(get_db()).update(product_id, json_body()))


@bp.post("/api/products/import")
@login_required_api
def api_import():
    """Add new products and update prices of existing ones (same name + unit). All or nothing."""
    upload = request.files.get("file")
    raw_bytes = upload.read() if upload is not None and upload.filename else b""
    return jsonify(ProductExcelService(get_db()).import_file(raw_bytes))
