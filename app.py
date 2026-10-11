"""Start sari-utang: flask --app app run --debug

The app itself is the sari_utang package (sari_utang/__init__.py: create_app).
"""

from sari_utang import create_app

app = create_app()
