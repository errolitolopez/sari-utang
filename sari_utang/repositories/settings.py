"""The settings table: simple key/value pairs, e.g. the hashed login PIN."""

from sari_utang.repositories.base import Repository


class SettingsRepository(Repository):
    def get(self, key):
        """The saved value, or None."""
        row = self.one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else None

    def set(self, key, value):
        self.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
