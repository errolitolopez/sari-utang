"""Login with the PIN, and setting the PIN."""

import time

from werkzeug.security import check_password_hash, generate_password_hash

from sari_utang.domain.pin import MAX_PIN_LENGTH, MIN_PIN_LENGTH, is_valid_pin
from sari_utang.errors import (
    ServiceUnavailableError, TooManyRequestsError, UnauthorizedError, ValidationError,
)
from sari_utang.services.base import Service

PIN_KEY = "pin_hash"


class LoginThrottle:
    """After too many wrong PINs, block that device for a while so the PIN can't be guessed."""

    MAX_ATTEMPTS = 5
    LOCK_SECONDS = 5 * 60

    def __init__(self):
        self.failed = {}  # ip address -> {"count": wrong tries, "locked_until": timestamp}

    def check(self, key):
        record = self.failed.get(key, {"count": 0, "locked_until": 0})
        wait = int(record["locked_until"] - time.time())
        if wait > 0:
            raise TooManyRequestsError(f"Too many wrong PINs. Try again in {wait // 60 + 1} min.")

    def wrong(self, key):
        record = self.failed.get(key, {"count": 0, "locked_until": 0})
        record["count"] += 1
        if record["count"] >= self.MAX_ATTEMPTS:
            record = {"count": 0, "locked_until": time.time() + self.LOCK_SECONDS}
        self.failed[key] = record

    def passed(self, key):
        self.failed.pop(key, None)

    def reset(self):
        self.failed.clear()


class AuthService(Service):
    def login(self, pin, ip, throttle):
        """Check the PIN. Raises an error when it is wrong, locked out or not set."""
        throttle.check(ip)
        pin_hash = self.settings.get(PIN_KEY)
        if pin_hash is None:
            raise ServiceUnavailableError("No PIN set yet. Run: flask --app app set-pin")
        if not check_password_hash(pin_hash, str(pin or "")):
            throttle.wrong(ip)
            raise UnauthorizedError("Wrong PIN.")
        throttle.passed(ip)

    def has_pin(self):
        return self.settings.get(PIN_KEY) is not None

    def set_pin(self, pin):
        """Save the login PIN. Only the hash is saved, never the PIN itself."""
        if not is_valid_pin(pin):
            raise ValidationError(f"PIN must be {MIN_PIN_LENGTH} to {MAX_PIN_LENGTH} digits.")
        self.settings.set(PIN_KEY, generate_password_hash(pin))
        self.commit()
