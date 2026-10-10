// Customer list: highest utang first, one page at a time (search is done on the server),
// and adds new ones.

const PER_PAGE = 20;
let page = 1; // the page being shown
let pages = 1; // how many pages there are for the current search
let loadNumber = 0; // only the newest request updates the list (typing fast sends several)

const list = document.getElementById("customer-list");
const searchInput = document.getElementById("search");
const modalElement = document.getElementById("add-customer-modal");
const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
const form = document.getElementById("add-customer-form");
const nameInput = document.getElementById("customer-name");
const phoneInput = document.getElementById("customer-phone");
const saveButton = document.getElementById("add-customer-button");

// One row: name and phone on the left, balance on the right. Tapping it opens the customer.
// textContent is used (not innerHTML) so names can't inject HTML.
function customerItem(customer) {
  const row = document.createElement("a");
  row.href = `/customers/${customer.id}`;
  row.className =
    "list-group-item list-group-item-action d-flex justify-content-between align-items-center";

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

  row.append(left, balance);
  return row;
}

function messageItem(text) {
  const div = document.createElement("div");
  div.className = "list-group-item text-body-secondary";
  div.textContent = text;
  return div;
}

// Highest utang first; the server does the sorting, searching and paging.
function render(data) {
  if (data.all_count === 0) {
    list.replaceChildren(messageItem("No customers yet. Tap + Add to add one."));
  } else if (data.customers.length === 0) {
    list.replaceChildren(messageItem("No customer matches your search."));
  } else {
    list.replaceChildren(...data.customers.map(customerItem));
  }

  document.getElementById("customer-summary").textContent =
    searchInput.value.trim() !== ""
      ? `${data.total} found`
      : `${data.all_count} total · ${data.with_utang_count} may utang`;

  // ‹ Prev · Page 2 of 3 · Next ›
  page = data.page;
  pages = data.pages;
  document.getElementById("pager").classList.toggle("d-none", pages <= 1);
  document.getElementById("page-info").textContent = `Page ${page} of ${pages}`;
  document.getElementById("prev-page").disabled = page <= 1;
  document.getElementById("next-page").disabled = page >= pages;
}

// Loads one page of customers from the server.
async function loadCustomers() {
  const thisLoad = ++loadNumber;
  const query = encodeURIComponent(searchInput.value.trim());
  try {
    const response = await apiFetch(`/api/customers?page=${page}&per_page=${PER_PAGE}&q=${query}`);
    if (!response || thisLoad !== loadNumber) return; // a newer search is on its way
    if (!response.ok) {
      showError("customers-error", "Could not load customers.");
      return;
    }
    hideError("customers-error");
    render(await response.json());
  } catch (error) {
    console.error(error);
    showError("customers-error", "Cannot reach the server. Check your connection.");
  }
}

function goToPage(newPage) {
  page = newPage;
  loadCustomers();
  window.scrollTo({ top: 0 });
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

document.getElementById("prev-page").addEventListener("click", () => goToPage(page - 1));
document.getElementById("next-page").addEventListener("click", () => goToPage(page + 1));

// Search after a short pause in typing, starting again from page 1.
let searchTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    page = 1;
    loadCustomers();
  }, 250);
});

loadCustomers();
