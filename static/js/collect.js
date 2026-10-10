// Singilin: customers who owe, longest-waiting utang first, with a "days" filter.

let customers = []; // from /api/collect
let overdueDays = 30; // from config/settings.json: this many days or more = "matagal"
let minDays = null; // the selected filter (0 = everyone who owes)

const list = document.getElementById("collect-list");
const filters = document.getElementById("filters");

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text; // textContent: names can't inject HTML
  return element;
}

function daysText(days) {
  if (days === 0) return "today";
  return days === 1 ? "1 day" : `${days} days`;
}

// One customer. Red when the utang has waited "overdueDays" or longer. Tap to open.
function customerRow(customer) {
  const isOverdue = customer.days >= overdueDays;
  const row = makeElement("a", "list-group-item list-group-item-action");
  row.href = `/customers/${customer.id}`;

  const top = makeElement("div", "d-flex justify-content-between align-items-center");
  const name = makeElement("span", "fw-semibold", customer.name);
  const balance = makeElement("span", "fw-semibold text-danger", formatAmount(customer.balance));
  top.append(name, balance);

  const bottom = makeElement("div", "d-flex justify-content-between align-items-center small");
  const since = makeElement("span", "text-body-secondary", `since ${customer.unpaid_since.slice(0, 10)}`);
  const days = makeElement(
    "span",
    `badge ${isOverdue ? "text-bg-danger" : "text-bg-secondary"}`,
    daysText(customer.days)
  );
  bottom.append(since, days);

  const details = [];
  if (customer.phone) details.push(customer.phone);
  details.push(
    customer.last_payment ? `last bayad ${customer.last_payment.slice(0, 10)}` : "no bayad yet"
  );
  row.append(top, bottom, makeElement("div", "small text-body-secondary", details.join(" · ")));
  return row;
}

function renderFilters() {
  // 7, 15, 30 days plus the configured number, without duplicates, smallest first.
  const options = [...new Set([0, 7, 15, 30, overdueDays])].sort((a, b) => a - b);
  filters.replaceChildren(
    ...options.map((days) => {
      const count = customers.filter((c) => c.days >= days).length;
      const label = days === 0 ? `Lahat (${count})` : `${days}+ araw (${count})`;
      const button = makeElement(
        "button",
        `btn btn-sm ${days === minDays ? "btn-primary" : "btn-outline-primary"}`,
        label
      );
      button.type = "button";
      button.setAttribute("aria-pressed", String(days === minDays));
      button.addEventListener("click", () => {
        minDays = days;
        render();
      });
      return button;
    })
  );
}

function render() {
  renderFilters();
  const shown = customers.filter((c) => c.days >= minDays);
  const total = shown.reduce((sum, c) => sum + c.balance, 0);

  document.getElementById("collect-summary").textContent =
    `${shown.length} customer${shown.length === 1 ? "" : "s"} · ${formatAmount(total)}`;

  if (shown.length) {
    list.replaceChildren(...shown.map(customerRow));
  } else {
    const message = customers.length ? "Walang utang na ganito katagal. 🎉" : "Walang utang. 🎉";
    list.replaceChildren(makeElement("div", "list-group-item text-body-secondary", message));
  }
}

async function loadList() {
  try {
    const response = await apiFetch("/api/collect");
    if (!response) return;
    if (!response.ok) {
      showError("collect-error", "Could not load the list.");
      return;
    }
    const data = await response.json();
    customers = data.customers;
    overdueDays = data.overdue_days;
    if (minDays === null) minDays = overdueDays; // start with the "matagal" ones
    render();
  } catch {
    showError("collect-error", "Cannot reach the server. Check your connection.");
  }
}

loadList();
