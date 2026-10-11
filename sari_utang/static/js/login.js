// Sends the PIN to /api/login and opens the dashboard when it is correct.

const form = document.getElementById("login-form");
const pinInput = document.getElementById("pin");
const button = document.getElementById("login-button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("login-error");

  const pin = pinInput.value.trim();
  if (!/^\d{4,6}$/.test(pin)) {
    showError("login-error", "PIN must be 4 to 6 digits.");
    return;
  }

  setBusy(button, true);
  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin }),
    });

    if (response.ok) {
      window.location.href = "/dashboard";
      return;
    }
    const data = await response.json();
    showError("login-error", data.error || "Login failed.");
  } catch {
    showError("login-error", "Cannot reach the server. Check your connection.");
  } finally {
    setBusy(button, false);
    pinInput.value = "";
    pinInput.focus();
  }
});
