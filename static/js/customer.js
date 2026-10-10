// One customer: shows their balance and history, and adds new utang.

const customerId = Number(document.getElementById("customer-page").dataset.customerId);

let products = []; // product list, loaded when the utang form opens
let lines = []; // items in the utang being made: {productId, name, unit, price, quantity}
let balance = 0; // what the customer owes now, in centavos

const modalElement = document.getElementById("utang-modal");
const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
const searchInput = document.getElementById("product-search");
const results = document.getElementById("product-results");
const linesList = document.getElementById("utang-lines");
const noteInput = document.getElementById("utang-note");
const otherName = document.getElementById("other-name");
const otherPrice = document.getElementById("other-price");
const saveButton = document.getElementById("save-utang-button");

// --- Small helpers -----------------------------------------------------------

// "12.5" -> 1250 centavos, or null if it is not a valid price.
function parsePrice(text) {
  const cleaned = text.replace(/,/g, "").trim();
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  return Math.round(Number(cleaned) * 100);
}

// "0.5" -> 0.5, or null if it is not a valid quantity (more than 0, up to 3 decimals).
function parseQuantity(text) {
  const cleaned = String(text).trim();
  if (!/^\d+(\.\d{1,3})?$/.test(cleaned)) return null;
  const quantity = Number(cleaned);
  return quantity > 0 ? quantity : null;
}

// Preview only; the server computes the real amounts when saving.
function lineAmount(line) {
  return Math.round(line.price * line.quantity);
}

// "2 pc Coke Mismo", "0.5 kg Bigas", "1 × Yelo" (typed-in items have no unit)
function describeItem(item) {
  return item.unit
    ? `${item.quantity} ${item.unit} ${item.name}`
    : `${item.quantity} × ${item.name}`;
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text; // textContent: names can't inject HTML
  return element;
}

// --- Customer and history ----------------------------------------------------

function renderCustomer(customer) {
  document.title = `${customer.name} · Sari Utang`;
  document.getElementById("customer-name").textContent = customer.name;
  document.getElementById("customer-phone").textContent = customer.phone || "";
  const balanceText = document.getElementById("customer-balance");
  balanceText.textContent = formatAmount(customer.balance);
  balanceText.className = `fs-3 fw-bold ${customer.balance > 0 ? "text-danger" : "text-success"}`;

  balance = customer.balance;
  // Nothing to pay when there is no utang.
  document.getElementById("add-payment-button").disabled = balance <= 0;
}

// What an entry is about: "2 bottle Coke Mismo, 0.5 kg Bigas" or "Bayad".
function describeTransaction(transaction) {
  if (transaction.items.length) return transaction.items.map(describeItem).join(", ");
  return transaction.type === "utang" ? "Utang" : "Bayad";
}

// One line per entry in the history. Tap it to see the details.
function historyItem(transaction) {
  const isUtang = transaction.type === "utang";
  const isVoided = transaction.voided_at !== null;
  const row = makeElement(
    "button",
    `list-group-item list-group-item-action ${isVoided ? "bg-body-tertiary" : ""}`
  );
  row.type = "button";

  // Voided entries are crossed out and greyed, so it's clear they don't count.
  const body = makeElement("div", isVoided ? "text-decoration-line-through text-body-secondary" : "");
  const top = makeElement("div", "d-flex justify-content-between");
  top.append(
    makeElement("span", "small text-body-secondary", transaction.date),
    makeElement(
      "span",
      `fw-semibold ${isVoided ? "" : isUtang ? "text-danger" : "text-success"}`,
      (isUtang ? "+" : "−") + formatAmount(transaction.amount)
    )
  );
  const bottom = makeElement("div", "d-flex justify-content-between align-items-center gap-2");
  bottom.append(
    makeElement("span", "text-truncate", describeTransaction(transaction)),
    makeElement("span", "text-body-secondary", "›")
  );
  body.append(top, bottom);
  row.append(body);

  if (isVoided) {
    row.append(makeElement("span", "badge text-bg-danger mt-1", "VOIDED"));
  }
  row.addEventListener("click", () => openDetails(transaction));
  return row;
}

// --- Details (view only) -----------------------------------------------------

const detailsModalElement = document.getElementById("details-modal");
const detailsModal = bootstrap.Modal.getOrCreateInstance(detailsModalElement);
let detailsTransaction = null; // the entry shown in the details popup

// One item: "Coke Mismo" / "2 bottle × ₱20.00" on the left, the amount on the right.
function detailsItem(item) {
  const li = makeElement("li", "list-group-item d-flex justify-content-between align-items-center");
  const left = makeElement("div");
  const quantity = item.unit ? `${item.quantity} ${item.unit}` : `${item.quantity}`;
  left.append(
    makeElement("div", "", item.name),
    makeElement("div", "small text-body-secondary", `${quantity} × ${formatAmount(item.price)}`)
  );
  li.append(left, makeElement("span", "fw-semibold", formatAmount(item.amount)));
  return li;
}

function openDetails(transaction) {
  detailsTransaction = transaction;
  const isUtang = transaction.type === "utang";
  const isVoided = transaction.voided_at !== null;

  document.getElementById("details-title").textContent = isUtang ? "Utang" : "Bayad";
  document.getElementById("details-date").textContent = transaction.date;

  const voided = document.getElementById("details-voided");
  voided.classList.toggle("d-none", !isVoided);
  if (isVoided) {
    voided.textContent = ["VOIDED " + transaction.voided_at, transaction.void_reason]
      .filter(Boolean)
      .join(" · ");
  }

  const items = document.getElementById("details-items");
  items.replaceChildren(...transaction.items.map(detailsItem));
  items.classList.toggle("d-none", transaction.items.length === 0);

  const total = document.getElementById("details-total");
  total.textContent = (isUtang ? "+" : "−") + formatAmount(transaction.amount);
  total.className = isVoided
    ? "text-decoration-line-through text-body-secondary"
    : isUtang ? "text-danger" : "text-success";

  // Payments with sukli: show the cash received and the change.
  const cash = document.getElementById("details-cash");
  cash.classList.toggle("d-none", !transaction.tendered);
  if (transaction.tendered) {
    cash.textContent =
      `Natanggap ${formatAmount(transaction.tendered)} · ` +
      `Sukli ${formatAmount(transaction.tendered - transaction.amount)}`;
  }

  document.getElementById("details-note").classList.toggle("d-none", !transaction.note);
  document.getElementById("details-note-text").textContent = transaction.note || "";

  // Already voided entries can't be voided again.
  document.getElementById("details-void-button").classList.toggle("d-none", isVoided);
  detailsModal.show();
}

// Void from the details: close the details first, then open the void popup.
document.getElementById("details-void-button").addEventListener("click", () => {
  detailsModalElement.addEventListener(
    "hidden.bs.modal",
    () => openVoidForm(detailsTransaction),
    { once: true }
  );
  detailsModal.hide();
});

async function loadCustomer() {
  try {
    const response = await apiFetch(`/api/customers/${customerId}/transactions`);
    if (!response) return;
    if (!response.ok) {
      showError("customer-error", "Could not load this customer.");
      return;
    }
    const data = await response.json();
    renderCustomer(data.customer);
    const history = document.getElementById("history");
    history.replaceChildren(
      ...(data.transactions.length
        ? data.transactions.map(historyItem)
        : [makeElement("div", "list-group-item text-body-secondary", "No utang yet.")])
    );
  } catch {
    showError("customer-error", "Cannot reach the server. Check your connection.");
  }
}

// --- Utang form --------------------------------------------------------------

function renderResults() {
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    results.replaceChildren();
    return;
  }
  const matches = products.filter((p) => p.name.toLowerCase().includes(query)).slice(0, 8);
  if (!matches.length) {
    results.replaceChildren(
      makeElement("div", "list-group-item text-body-secondary small", "No product found. Use \"Item not in the list?\" below.")
    );
    return;
  }
  results.replaceChildren(
    ...matches.map((product) => {
      const button = makeElement(
        "button",
        "list-group-item list-group-item-action d-flex justify-content-between"
      );
      button.type = "button";
      button.append(
        makeElement("span", "", product.name),
        makeElement("span", "text-body-secondary", `${formatAmount(product.price)} / ${product.unit}`)
      );
      button.addEventListener("click", () => addProduct(product));
      return button;
    })
  );
}

// Tapping a product adds 1; tapping it again adds 1 more to the same line.
function addProduct(product) {
  const existing = lines.find((line) => line.productId === product.id);
  if (existing) {
    existing.quantity = Number((existing.quantity + 1).toFixed(3));
  } else {
    lines.push({
      productId: product.id,
      name: product.name,
      unit: product.unit,
      price: product.price,
      quantity: 1,
    });
  }
  searchInput.value = "";
  renderResults();
  renderLines();
  searchInput.focus();
}

function addOtherItem() {
  hideError("utang-error");
  const name = otherName.value.trim();
  const price = parsePrice(otherPrice.value);
  if (!name) {
    showError("utang-error", "Type the item name.");
    otherName.focus();
    return;
  }
  if (!price) {
    showError("utang-error", "Enter a price like 5 or 12.50.");
    otherPrice.focus();
    return;
  }
  lines.push({ productId: null, name, unit: null, price, quantity: 1 });
  otherName.value = "";
  otherPrice.value = "";
  renderLines();
}

function renderTotal() {
  const allValid = lines.every((line) => line.quantity !== null);
  const total = lines.reduce((sum, line) => sum + (line.quantity ? lineAmount(line) : 0), 0);
  document.getElementById("utang-total").textContent = allValid ? formatAmount(total) : "—";
}

function lineItem(line, index) {
  const li = makeElement("li", "list-group-item");

  const top = makeElement("div", "d-flex justify-content-between align-items-start");
  const priceText = line.unit
    ? `${formatAmount(line.price)} / ${line.unit}`
    : formatAmount(line.price);
  const info = makeElement("div");
  info.append(makeElement("div", "", line.name), makeElement("div", "small text-body-secondary", priceText));

  const remove = makeElement("button", "btn btn-sm btn-outline-secondary", "×");
  remove.type = "button";
  remove.setAttribute("aria-label", `Remove ${line.name}`);
  remove.addEventListener("click", () => {
    lines.splice(index, 1);
    renderLines();
  });
  top.append(info, remove);

  const bottom = makeElement("div", "d-flex justify-content-between align-items-center mt-2");
  const group = makeElement("div", "input-group input-group-sm");
  group.style.maxWidth = "160px";
  const quantityInput = makeElement("input", "form-control");
  quantityInput.inputMode = "decimal";
  quantityInput.value = line.quantity;
  quantityInput.setAttribute("aria-label", `Quantity of ${line.name}`);
  group.append(quantityInput, makeElement("span", "input-group-text", line.unit || "×"));

  const amount = makeElement("span", "fw-semibold", formatAmount(lineAmount(line)));
  quantityInput.addEventListener("input", () => {
    line.quantity = parseQuantity(quantityInput.value);
    quantityInput.classList.toggle("is-invalid", line.quantity === null);
    amount.textContent = line.quantity === null ? "—" : formatAmount(lineAmount(line));
    renderTotal();
  });
  bottom.append(group, amount);

  li.append(top, bottom);
  return li;
}

function renderLines() {
  linesList.replaceChildren(
    ...(lines.length
      ? lines.map(lineItem)
      : [makeElement("li", "list-group-item text-body-secondary", "No items yet. Search a product above.")])
  );
  renderTotal();
}

async function openUtangForm() {
  lines = [];
  noteInput.value = "";
  searchInput.value = "";
  otherName.value = "";
  otherPrice.value = "";
  hideError("utang-error");
  renderResults();
  renderLines();
  modal.show();

  try {
    const response = await apiFetch("/api/products");
    if (!response) return;
    products = response.ok ? (await response.json()).products : [];
    if (!response.ok) showError("utang-error", "Could not load products.");
  } catch {
    showError("utang-error", "Cannot reach the server. Check your connection.");
  }
}

document.getElementById("utang-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("utang-error");

  if (!lines.length) {
    showError("utang-error", "Add at least one item.");
    return;
  }
  if (lines.some((line) => line.quantity === null)) {
    showError("utang-error", "Fix the quantities marked in red (e.g. 2 or 0.5).");
    return;
  }

  const items = lines.map((line) =>
    line.productId
      ? { product_id: line.productId, quantity: line.quantity }
      : { name: line.name, price: line.price, quantity: line.quantity }
  );

  saveButton.disabled = true;
  try {
    const response = await apiFetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "utang",
        customer_id: customerId,
        items,
        note: noteInput.value.trim(),
      }),
    });
    if (!response) return;
    const data = await response.json();
    if (!response.ok) {
      showError("utang-error", data.error || "Could not save the utang.");
      return;
    }
    modal.hide();
    await loadCustomer();
  } catch {
    showError("utang-error", "Cannot reach the server. Check your connection.");
  } finally {
    saveButton.disabled = false;
  }
});

// --- Payment form ------------------------------------------------------------

const paymentModal = bootstrap.Modal.getOrCreateInstance(document.getElementById("payment-modal"));
const paymentAmount = document.getElementById("payment-amount");
const paymentNote = document.getElementById("payment-note");
const savePaymentButton = document.getElementById("save-payment-button");

// Shows what will be left after this payment as you type.
// Paying more than the utang counts as paid in full; the extra is the sukli.
function renderRemaining() {
  const amount = parsePrice(paymentAmount.value);
  const remaining = document.getElementById("payment-remaining");
  const changeRow = document.getElementById("payment-change-row");
  const change = amount ? amount - balance : 0;

  if (!amount) {
    remaining.textContent = "—";
    remaining.className = "fw-semibold";
  } else {
    const left = Math.max(balance - amount, 0);
    remaining.textContent = formatAmount(left);
    remaining.className = `fw-semibold ${left === 0 ? "text-success" : ""}`;
  }

  changeRow.classList.toggle("d-none", change <= 0);
  document.getElementById("payment-change").textContent = change > 0 ? formatAmount(change) : "";
}

function showMessage(message) {
  document.getElementById("customer-message-text").textContent = message;
  document.getElementById("customer-message").classList.remove("d-none");
}

function openPaymentForm() {
  document.getElementById("payment-owed").textContent = formatAmount(balance);
  paymentAmount.value = "";
  paymentNote.value = "";
  hideError("payment-error");
  renderRemaining();
  paymentModal.show();
}

document.getElementById("pay-full-button").addEventListener("click", () => {
  paymentAmount.value = (balance / 100).toFixed(2);
  renderRemaining();
});

document.getElementById("payment-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("payment-error");

  const amount = parsePrice(paymentAmount.value);
  if (!amount) {
    showError("payment-error", "Enter an amount like 50 or 12.50.");
    paymentAmount.focus();
    return;
  }

  savePaymentButton.disabled = true;
  try {
    const response = await apiFetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "payment",
        customer_id: customerId,
        amount,
        note: paymentNote.value.trim(),
      }),
    });
    if (!response) return;
    const data = await response.json();
    if (!response.ok) {
      showError("payment-error", data.error || "Could not save the payment.");
      return;
    }
    paymentModal.hide();
    showMessage(
      data.change > 0
        ? `Bayad lahat ${formatAmount(data.transaction.amount)} · Sukli ${formatAmount(data.change)}`
        : `Bayad ${formatAmount(data.transaction.amount)} saved.`
    );
    await loadCustomer();
  } catch {
    showError("payment-error", "Cannot reach the server. Check your connection.");
  } finally {
    savePaymentButton.disabled = false;
  }
});

document.getElementById("payment-modal").addEventListener("shown.bs.modal", () => paymentAmount.focus());
paymentAmount.addEventListener("input", renderRemaining);
document.getElementById("add-payment-button").addEventListener("click", openPaymentForm);

// --- Void --------------------------------------------------------------------

const voidModal = bootstrap.Modal.getOrCreateInstance(document.getElementById("void-modal"));
const voidReason = document.getElementById("void-reason");
const confirmVoidButton = document.getElementById("confirm-void-button");
let voidingId = null; // the transaction shown in the void popup

function openVoidForm(transaction) {
  voidingId = transaction.id;
  const isUtang = transaction.type === "utang";
  const summary = document.getElementById("void-summary");
  summary.replaceChildren(
    makeElement(
      "div",
      `fw-semibold ${isUtang ? "text-danger" : "text-success"}`,
      `${isUtang ? "Utang" : "Bayad"} ${formatAmount(transaction.amount)}`
    ),
    makeElement("div", "", describeTransaction(transaction)),
    makeElement("div", "small text-body-secondary", transaction.date)
  );
  voidReason.value = "";
  hideError("void-error");
  voidModal.show();
}

document.getElementById("void-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("void-error");

  confirmVoidButton.disabled = true;
  try {
    const response = await apiFetch(`/api/transactions/${voidingId}/void`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: voidReason.value.trim() }),
    });
    if (!response) return;
    const data = await response.json();
    if (!response.ok) {
      showError("void-error", data.error || "Could not void this entry.");
      return;
    }
    voidModal.hide();
    await loadCustomer();
  } catch {
    showError("void-error", "Cannot reach the server. Check your connection.");
  } finally {
    confirmVoidButton.disabled = false;
  }
});

// --- Start -------------------------------------------------------------------

document.getElementById("add-utang-button").addEventListener("click", openUtangForm);
document.getElementById("add-other-button").addEventListener("click", addOtherItem);
// Enter in the "other item" fields adds the item instead of saving the whole utang.
for (const input of [otherName, otherPrice]) {
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addOtherItem();
  });
}
modalElement.addEventListener("shown.bs.modal", () => searchInput.focus());
searchInput.addEventListener("input", renderResults);

// Enter in the search box adds the first match instead of submitting the form.
searchInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  const first = results.querySelector("button");
  if (first) first.click();
});

loadCustomer();
