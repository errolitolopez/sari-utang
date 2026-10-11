"""The set-pin command: flask --app app set-pin"""

import click
from flask.cli import with_appcontext

from sari_utang.database import get_db
from sari_utang.errors import ValidationError
from sari_utang.services import AuthService


@click.command("set-pin")
@with_appcontext
@click.password_option("--pin", prompt="New PIN", help="4 to 6 digits.")
def set_pin_command(pin):
    """Set or change the login PIN."""
    try:
        AuthService(get_db()).set_pin(pin)
    except ValidationError as error:
        raise click.BadParameter(error.message)
    click.echo("PIN saved.")
