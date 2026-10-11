// Helpers shared by the logged-in pages (dashboard, customers).

const peso = new Intl.NumberFormat("en-PH", { style: "currency", currency: "PHP" });

// Amounts from the server are in centavos (1250 = P12.50).
function formatAmount(centavos) {
  return peso.format(centavos / 100);
}

function showError(elementId, message) {
  const box = document.getElementById(elementId);
  box.textContent = message;
  box.classList.remove("d-none");
}

function hideError(elementId) {
  document.getElementById(elementId).classList.add("d-none");
}

// fetch() that sends the user back to the login page when the session has ended.
// Returns null in that case, so callers can simply stop: if (!response) return;
async function apiFetch(url, options) {
  const response = await fetch(url, options);
  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }
  return response;
}

document.getElementById("logout-button").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
});
