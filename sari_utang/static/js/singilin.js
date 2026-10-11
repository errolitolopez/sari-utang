// Collections: customers who owe, longest-waiting credit first, with a "days" filter.

let customers = []; // from /api/singilin
let overdueDays = 30; // from config/settings.json: this many days or more = "overdue"
let minDays = null; // the selected filter (0 = everyone who owes)

const list = document.getElementById("singilin-list");
const filters = document.getElementById("filters");

// daysText(0) -> "today", daysText(1) -> "1 day", daysText(40) -> "40 days"
const daysText = (days) => {
  if (days === 0) return "today";
  return days === 1 ? "1 day" : `${days} days`;
};

// One customer. Red when the credit has waited "overdueDays" or longer. Tap to open.
const customerRow = (customer) => {
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
    customer.last_payment ? `last payment ${customer.last_payment.slice(0, 10)}` : "no payment yet"
  );
  row.append(top, bottom, makeElement("div", "small text-body-secondary", details.join(" · ")));
  return row;
};

// renderFilters() -> the "All (5)" / "30+ days (2)" buttons
const renderFilters = () => {
  // 7, 15, 30 days plus the configured number, without duplicates, smallest first.
  const options = [...new Set([0, 7, 15, 30, overdueDays])].sort((a, b) => a - b);
  filters.replaceChildren(
    ...options.map((days) => {
      const count = customers.filter((c) => c.days >= days).length;
      const label = days === 0 ? `All (${count})` : `${days}+ days (${count})`;
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
};

// render() -> the filter buttons, the summary line, the ZIP link and the rows
const render = () => {
  renderFilters();
  const shown = customers.filter((c) => c.days >= minDays);
  const total = shown.reduce((sum, c) => sum + c.balance, 0);

  document.getElementById("singilin-summary").textContent =
    `${shown.length} customer${shown.length === 1 ? "" : "s"} · ${formatAmount(total)}`;

  // The ZIP has one PDF invoice for each customer shown, so it follows the filter.
  const zip = document.getElementById("download-zip");
  zip.href = `/singilin/invoices.zip?min_days=${minDays}`;
  zip.textContent = `Download invoices (ZIP, ${shown.length})`;
  zip.classList.toggle("disabled", shown.length === 0);
  zip.setAttribute("aria-disabled", String(shown.length === 0));

  if (shown.length) {
    list.replaceChildren(...shown.map(customerRow));
  } else {
    const message = customers.length ? "No credit this old. 🎉" : "No credit. 🎉";
    list.replaceChildren(makeElement("div", "list-group-item text-body-secondary", message));
  }
};

// loadList() -> fetches /api/singilin and draws it
const loadList = async () => {
  try {
    const response = await apiFetch("/api/singilin");
    if (!response) return;
    if (!response.ok) {
      showError("singilin-error", "Could not load the list.");
      return;
    }
    const data = await response.json();
    customers = data.customers;
    overdueDays = data.overdue_days;
    if (minDays === null) minDays = overdueDays; // start with the "overdue" ones
    render();
  } catch (error) {
    console.error(error); // shows the real cause in the browser console (F12)
    showError("singilin-error", "Cannot reach the server. Check your connection.");
  }
};

loadList();
