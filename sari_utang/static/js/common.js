// Helpers shared by the logged-in pages (dashboard, customers).

const peso = new Intl.NumberFormat("en-PH", { style: "currency", currency: "PHP" });

// Amounts from the server are in centavos (1250 = P12.50).
// formatAmount(1250) -> "₱12.50"
const formatAmount = (centavos) => {
  return peso.format(centavos / 100);
};

// showError("customers-error", "Could not load customers.") -> fills that error box and shows it
const showError = (elementId, message) => {
  const box = document.getElementById(elementId);
  box.textContent = message;
  box.classList.remove("d-none");
};

// hideError("customers-error") -> hides that error box
const hideError = (elementId) => {
  document.getElementById(elementId).classList.add("d-none");
};

// fetch() that sends the user back to the login page when the session has ended.
// Returns null in that case, so callers can simply stop: if (!response) return;
// apiFetch("/api/customers") -> the response, or null
const apiFetch = async (url, options) => {
  const response = await fetch(url, options);
  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }
  return response;
};

// makeElement("span", "fw-semibold", "Hi") -> <span class="fw-semibold">Hi</span>
// textContent is used (not innerHTML) so names can't inject HTML.
const makeElement = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

// messageItem("No customers yet.") -> a grey list row, for an empty list or a message
const messageItem = (text) => makeElement("div", "list-group-item text-body-secondary", text);

// setBusy(saveButton, true) -> the button is disabled and shows a spinner; setBusy(saveButton, false) restores it
const setBusy = (button, busy) => {
  button.disabled = busy;
  button.querySelector(".spinner-border")?.remove();
  if (busy) {
    const spinner = makeElement("span", "spinner-border spinner-border-sm me-2");
    spinner.setAttribute("aria-hidden", "true");
    button.prepend(spinner);
  }
};

// The logout button is in the navbar, which the login page doesn't have.
document.getElementById("logout-button")?.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
});
