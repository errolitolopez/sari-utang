// Loads the summary from /api/dashboard and fills in the page.

// Builds one list row that opens the customer when tapped.
// textContent is used (not innerHTML) so names can't inject HTML.
// listItem(3, "Aling Nena", "2026-10-10", "₱50.00", "text-danger") -> a row linking to /customers/3
const listItem = (customerId, title, subtitle, amountText, amountClass) => {
  const li = document.createElement("a");
  li.href = `/customers/${customerId}`;
  li.className =
    "list-group-item list-group-item-action d-flex justify-content-between align-items-center";

  const left = document.createElement("div");
  const name = document.createElement("div");
  name.textContent = title;
  left.append(name);
  if (subtitle) {
    const small = document.createElement("div");
    small.className = "small text-body-secondary";
    small.textContent = subtitle;
    left.append(small);
  }

  const amount = document.createElement("span");
  amount.className = `fw-semibold ${amountClass}`;
  amount.textContent = amountText;

  li.append(left, amount);
  return li;
};

// render(data) -> the totals, the biggest balances and the recent transactions
const render = (data) => {
  document.getElementById("total-outstanding").textContent = formatAmount(data.total_outstanding);
  document.getElementById("customers-with-utang").textContent = data.customers_with_utang;
  document.getElementById("customer-count").textContent = data.customer_count;
  document.getElementById("overdue-days").textContent = data.overdue_days;
  document.getElementById("overdue-count").textContent =
    data.overdue_count === 1 ? "1 customer" : `${data.overdue_count} customers`;
  // Highlight the card only when someone needs to be reminded.
  const card = document.getElementById("overdue-card");
  card.classList.toggle("border-warning", data.overdue_count > 0);
  card.classList.toggle("text-bg-warning", data.overdue_count > 0);

  const top = document.getElementById("top-balances");
  top.replaceChildren(
    ...(data.top_balances.length
      ? data.top_balances.map((c) => listItem(c.id, c.name, "", formatAmount(c.balance), "text-danger"))
      : [messageItem("Walang utang. 🎉")])
  );

  const recent = document.getElementById("recent-transactions");
  recent.replaceChildren(
    ...(data.recent_transactions.length
      ? data.recent_transactions.map((t) => {
          const isUtang = t.type === "utang";
          const subtitle = [t.date, t.note].filter(Boolean).join(" · ");
          return listItem(
            t.customer_id,
            t.customer_name,
            subtitle,
            (isUtang ? "+" : "−") + formatAmount(t.amount),
            isUtang ? "text-danger" : "text-success"
          );
        })
      : [messageItem("No transactions yet.")])
  );
};

// loadDashboard() -> fetches /api/dashboard and fills in the page
const loadDashboard = async () => {
  try {
    const response = await apiFetch("/api/dashboard");
    if (!response) return;
    if (!response.ok) {
      showError("dashboard-error", "Could not load the dashboard.");
      return;
    }
    render(await response.json());
  } catch {
    showError("dashboard-error", "Cannot reach the server. Check your connection.");
  }
};

loadDashboard();
