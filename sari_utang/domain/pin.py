"""Rules for the login PIN."""

MIN_PIN_LENGTH = 4
MAX_PIN_LENGTH = 6


def is_valid_pin(pin):
    return pin.isdigit() and MIN_PIN_LENGTH <= len(pin) <= MAX_PIN_LENGTH
