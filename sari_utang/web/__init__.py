"""The Flask side: one blueprint per area (pages + JSON API), kept thin. A route reads the
request, calls a service, and returns JSON or a page; errors from services become JSON answers
(sari_utang.errors)."""

from sari_utang.web import auth, customers, dashboard, invoices, products, singilin, transactions

BLUEPRINTS = [auth.bp, dashboard.bp, customers.bp, products.bp, transactions.bp, singilin.bp,
              invoices.bp]
