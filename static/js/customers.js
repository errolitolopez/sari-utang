// Customer list: loads all customers, filters them as you type, and adds new ones.

let customers = []; // everything from /api/customers, filtered on the page

const list = document.getElementById("customer-list");
const searchInput = document.getElementById("search");
const modalElement = document.getElementById("add-customer-modal");
const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
const form = document.getElementById("add-customer-form");
const nameInput = document.getElementById("customer-name");
const phoneInput = document.getElementById("customer-phone");
const saveButton = document.getElementById("add-customer-button");

// One row: name and phone on the left, balance on the right.
// textContent is used (not innerHTML) so names can't inject HTML.
function customerItem(customer) {
  const li = document.createElement("li");
  li.className = "list-group-item d-flex justify-content-between align-items-center";

  const left = document.createElement("div");
  const name = document.createElement("div");
  name.textContent = customer.name;
  left.append(name);
  if (customer.phone) {
    const phone = document.createElement("div");
    phone.className = "small text-body-secondary";
    phone.textContent = customer.phone;
    left.append(phone);
  }

  const balance = document.createElement("span");
  if (customer.balance > 0) {
    balance.className = "fw-semibold text-danger";
    balance.textContent = formatAmount(customer.balance);
  } else {
    balance.className = "small text-body-secondary";
    balance.textContent = "Walang utang";
  }

  li.append(left, balance);
  return li;
}

function messageItem(text) {
  const li = document.createElement("li");
  li.className = "list-group-item text-body-secondary";
  li.textContent = text;
  return li;
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  const shown = customers.filter(
    (c) => c.name.toLowerCase().includes(query) || (c.phone || "").includes(query)
  );

  if (customers.length === 0) {
    list.replaceChildren(messageItem("No customers yet. Tap + Add to add one."));
  } else if (shown.length === 0) {
    list.replaceChildren(messageItem("No customer matches your search."));
  } else {
    list.replaceChildren(...shown.map(customerItem));
  }

  const withUtang = customers.filter((c) => c.balance > 0).length;
  document.getElementById("customer-summary").textContent =
    `${customers.length} total · ${withUtang} may utang`;
}

async function loadCustomers() {
  try {
    const response = await apiFetch("/api/customers");
    if (!response) return;
    if (!response.ok) {
      showError("customers-error", "Could not load customers.");
      return;
    }
    customers = (await response.json()).customers;
    render();
  } catch {
    showError("customers-error", "Cannot reach the server. Check your connection.");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("add-customer-error");

  const name = nameInput.value.trim();
  if (!name) {
    showError("add-customer-error", "Name is required.");
    nameInput.focus();
    return;
  }

  saveButton.disabled = true;
  try {
    const response = await apiFetch("/api/customers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone: phoneInput.value.trim() }),
    });
    if (!response) return;
    const data = await response.json();
    if (!response.ok) {
      showError("add-customer-error", data.error || "Could not save the customer.");
      return;
    }
    modal.hide();
    searchInput.value = "";
    await loadCustomers();
  } catch {
    showError("add-customer-error", "Cannot reach the server. Check your connection.");
  } finally {
    saveButton.disabled = false;
  }
});

// Start each popup with an empty form, and put the cursor in the name field.
modalElement.addEventListener("show.bs.modal", () => {
  form.reset();
  hideError("add-customer-error");
});
modalElement.addEventListener("shown.bs.modal", () => nameInput.focus());

searchInput.addEventListener("input", render);

loadCustomers();
