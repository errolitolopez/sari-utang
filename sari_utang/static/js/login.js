// Sends the PIN to /api/login and opens the dashboard when it is correct.

const form = document.getElementById("login-form");
const pinInput = document.getElementById("pin");
const errorBox = document.getElementById("login-error");
const button = document.getElementById("login-button");

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("d-none");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.classList.add("d-none");

  const pin = pinInput.value.trim();
  if (!/^\d{4,6}$/.test(pin)) {
    showError("PIN must be 4 to 6 digits.");
    return;
  }

  button.disabled = true;
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
    showError(data.error || "Login failed.");
  } catch {
    showError("Cannot reach the server. Check your connection.");
  } finally {
    button.disabled = false;
    pinInput.value = "";
    pinInput.focus();
  }
});
