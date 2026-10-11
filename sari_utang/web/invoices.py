"""A customer's invoice: page, PDF, and the ZIP of everyone's PDFs."""

import io

from flask import Blueprint, abort, render_template, request, send_file

from sari_utang.database import get_db
from sari_utang.services import InvoiceService
from sari_utang.web.security import login_required_page

bp = Blueprint("invoices", __name__)


@bp.get("/customers/<int:customer_id>/invoice")
@login_required_page
def page(customer_id):
    service = InvoiceService(get_db())
    if not service.exists(customer_id):
        abort(404)
    return render_template("invoice.html", **service.page(customer_id))


@bp.get("/customers/<int:customer_id>/invoice.pdf")
@login_required_page
def pdf(customer_id):
    service = InvoiceService(get_db())
    if not service.exists(customer_id):
        abort(404)
    data, filename = service.pdf(customer_id)
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True,
                     download_name=filename)


@bp.get("/singilin/invoices.zip")
@login_required_page
def zip_download():
    """One PDF invoice per customer with debt, in one ZIP.

    ?min_days=30 only includes customers whose oldest unpaid debt is 30+ days old
    (the same filter as the Collections page). Without it, everyone with debt.
    """
    data, filename = InvoiceService(get_db()).zip_of_all(request.args.get("min_days", default=0, type=int))
    return send_file(io.BytesIO(data), mimetype="application/zip", as_attachment=True,
                     download_name=filename)
