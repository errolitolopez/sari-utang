"""Make invoice PDFs: a small A6 receipt, the same layout as the invoice page.

Uses fpdf2 (pure Python, no browser needed) and the DejaVu Sans font in fonts/,
because the built-in PDF fonts don't have the peso sign.
"""

import os
from decimal import Decimal

from fpdf import FPDF

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

GREY = (108, 117, 125)
BLACK = (33, 37, 41)
AMOUNT_WIDTH = 22  # mm, the right-hand column for amounts
LINE = 4.2  # mm, height of one line of text


def peso(centavos):
    """1250 -> "₱12.50" """
    return f"₱{centavos / 100:,.2f}"


def qty(quantity):
    """2.0 -> "2", 0.5 -> "0.5" """
    return f"{Decimal(str(quantity)).normalize():f}"


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__(unit="mm", format=(105, 148))  # A6: a quarter of a bond paper
        self.set_margins(6, 6, 6)
        self.set_auto_page_break(auto=True, margin=6)
        self.add_font("DejaVu", "", os.path.join(FONTS_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf"))

    def text_style(self, size=8, bold=False, grey=False):
        self.set_font("DejaVu", "B" if bold else "", size)
        self.set_text_color(*(GREY if grey else BLACK))

    def dashed_line(self):
        self.set_draw_color(173, 181, 189)
        self.set_dash_pattern(dash=0.6, gap=0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_dash_pattern()
        self.ln(1.2)

    def row(self, left, right, size=8, bold=False, grey_left=False):
        """Text on the left (wraps if long), amount on the right."""
        self.text_style(size, bold, grey_left)
        left_width = self.epw - AMOUNT_WIDTH
        lines = self.multi_cell(left_width, LINE, left, align="L", dry_run=True, output="LINES")
        height = LINE * len(lines)
        if self.will_page_break(height):
            self.add_page()
        y = self.get_y()
        self.multi_cell(left_width, LINE, left, align="L", new_x="RIGHT", new_y="TOP")
        self.text_style(size, bold)
        self.cell(AMOUNT_WIDTH, LINE, right, align="R")
        self.set_xy(self.l_margin, y + height)

    def right_row(self, label, amount, bold=False):
        """A small label and amount on the right, e.g. Subtotal."""
        self.text_style(7.5, grey=True)
        self.cell(self.epw - AMOUNT_WIDTH, LINE, label, align="R")
        self.text_style(8, bold)
        self.cell(AMOUNT_WIDTH, LINE, amount, align="R", new_x="LMARGIN", new_y="NEXT")


def invoice_pdf_bytes(store_name, customer, invoice, today):
    """The invoice as PDF bytes. invoice is what app.invoice_data() returns."""
    pdf = InvoicePDF()
    pdf.set_title(f"Utang ni {customer['name']}")
    pdf.add_page()

    # Header: store name and date, customer and phone
    pdf.text_style(10, bold=True)
    pdf.cell(pdf.epw / 2, 5, store_name)
    pdf.text_style(8, grey=True)
    pdf.cell(pdf.epw / 2, 5, today, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.text_style(8)
    pdf.cell(pdf.epw / 2, LINE, f"Utang ni {customer['name']}")
    pdf.text_style(8, grey=True)
    pdf.cell(pdf.epw / 2, LINE, customer["phone"] or "", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.8)
    pdf.dashed_line()

    if not invoice["entries"]:
        pdf.text_style(8)
        pdf.cell(0, 6, "Walang utang. Bayad na lahat.", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    # Unpaid utang, oldest first, one line per item
    for entry in invoice["entries"]:
        pdf.ln(0.8)
        pdf.text_style(7, bold=True, grey=True)
        heading = entry["date"][:10] + (f" · {entry['note']}" if entry["note"] else "")
        pdf.multi_cell(0, 3.6, heading, align="L", new_x="LMARGIN", new_y="NEXT")
        for item in entry["items"]:
            unit = f" {item['unit']}" if item["unit"] else ""
            pdf.row(f"{item['name']} · {qty(item['quantity'])}{unit} × {peso(item['price'])}",
                    peso(item["amount"]))
        if len(entry["items"]) > 1:
            pdf.right_row("Subtotal", peso(entry["amount"]), bold=True)
        if entry["paid"]:
            pdf.right_row("Bayad na (partial)", f"−{peso(entry['paid'])}")
            pdf.right_row("Natitira", peso(entry["remaining"]), bold=True)

    # Totals
    pdf.ln(1)
    pdf.dashed_line()
    pdf.row("Total utang", peso(invoice["total_utang"]))
    if invoice["partly_paid"]:
        pdf.row("Bayad na (partial)", f"−{peso(invoice['partly_paid'])}")
    pdf.row("Balance", peso(invoice["balance"]), size=10, bold=True)
    if invoice["last_payment"]:
        pdf.text_style(6.5, grey=True)
        pdf.cell(0, 4, f"Huling bayad: {invoice['last_payment'][:10]}", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
