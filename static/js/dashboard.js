// Loads the summary from /api/dashboard and fills in the page.

const peso = new Intl.NumberFormat("en-PH", { style: "currency", currency: "PHP" });

// Amounts from the server are in centavos (1250 = P12.50).
function formatAmount(centavos) {
  return peso.format(centavos / 100);
}

function showError(message) {
  const box = document.getElementById("dashboard-error");
  box.textContent = message;
  box.classList.remove("d-none");
}

// Builds one list row. textContent is used (not innerHTML) so names can't inject HTML.
function listItem(title, subtitle, amountText, amountClass) {
  const li = document.createElement("li");
  li.className = "list-group-item d-flex justify-content-between align-items-center";

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
}

function emptyItem(message) {
  const li = document.createElement("li");
  li.className = "list-group-item text-body-secondary";
  li.textContent = message;
  return li;
}

function render(data) {
  document.getElementById("total-outstanding").textContent = formatAmount(data.total_outstanding);
  document.getElementById("customers-with-utang").textContent = data.customers_with_utang;
  document.getElementById("customer-count").textContent = data.customer_count;

  const top = document.getElementById("top-balances");
  top.replaceChildren(
    ...(data.top_balances.length
      ? data.top_balances.map((c) => listItem(c.name, "", formatAmount(c.balance), "text-danger"))
      : [emptyItem("Walang utang. 🎉")])
  );

  const recent = document.getElementById("recent-transactions");
  recent.replaceChildren(
    ...(data.recent_transactions.length
      ? data.recent_transactions.map((t) => {
          const isUtang = t.type === "utang";
          const subtitle = [t.date, t.note].filter(Boolean).join(" · ");
          return listItem(
            t.customer_name,
            subtitle,
            (isUtang ? "+" : "−") + formatAmount(t.amount),
            isUtang ? "text-danger" : "text-success"
          );
        })
      : [emptyItem("No transactions yet.")])
  );
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      showError("Could not load the dashboard.");
      return;
    }
    render(await response.json());
  } catch {
    showError("Cannot reach the server. Check your connection.");
  }
}

document.getElementById("logout-button").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
});

loadDashboard();
