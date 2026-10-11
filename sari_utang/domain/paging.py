"""Paging of long lists."""

MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 20


def page_numbers(total, page, per_page):
    """Fix page / per_page from the address bar. Returns (page, per_page, pages, offset)."""
    per_page = min(max(per_page, 1), MAX_PER_PAGE)
    pages = max((total + per_page - 1) // per_page, 1)
    page = min(max(page, 1), pages)  # e.g. page 9 of 3 -> page 3
    return page, per_page, pages, (page - 1) * per_page
