// Product list: loads all products, filters them as you type, adds new ones,
// and edits a product when you tap it (prices change often).

let products = []; // everything from /api/products, filtered on the page
let editingId = null; // null = adding a new product, a number = editing that product

const list = document.getElementById("product-list");
const searchInput = document.getElementById("search");
const modalElement = document.getElementById("product-modal");
const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
const form = document.getElementById("product-form");
const modalTitle = document.getElementById("product-modal-title");
const nameInput = document.getElementById("product-name");
const priceInput = document.getElementById("product-price");
const unitSelect = document.getElementById("product-unit");
const saveButton = document.getElementById("save-product-button");

// "12.5" -> 1250 centavos. Returns null if it is not a valid price.
function parsePrice(text) {
  const cleaned = text.replace(/,/g, "").trim();
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  return Math.round(Number(cleaned) * 100);
}

// 1250 centavos -> "12.50" for the price field.
function priceForInput(centavos) {
  return (centavos / 100).toFixed(2);
}

// One row you can tap to edit. textContent is used so names can't inject HTML.
function productItem(product) {
  const button = document.createElement("button");
  button.type = "button";
  button.className =
    "list-group-item list-group-item-action d-flex justify-content-between align-items-center";

  const name = document.createElement("span");
  name.textContent = product.name;

  const price = document.createElement("span");
  price.className = "fw-semibold";
  price.textContent = `${formatAmount(product.price)} / ${product.unit}`;

  button.append(name, price);
  button.addEventListener("click", () => openForm(product));
  return button;
}

function messageItem(text) {
  const div = document.createElement("div");
  div.className = "list-group-item text-body-secondary";
  div.textContent = text;
  return div;
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  const shown = products.filter((p) => p.name.toLowerCase().includes(query));

  if (products.length === 0) {
    list.replaceChildren(messageItem("No products yet. Tap + Add to add one."));
  } else if (shown.length === 0) {
    list.replaceChildren(messageItem("No product matches your search."));
  } else {
    list.replaceChildren(...shown.map(productItem));
  }

  document.getElementById("product-summary").textContent = `${products.length} total`;
}

async function loadProducts() {
  try {
    const response = await apiFetch("/api/products");
    if (!response) return;
    if (!response.ok) {
      showError("products-error", "Could not load products.");
      return;
    }
    products = (await response.json()).products;
    render();
  } catch {
    showError("products-error", "Cannot reach the server. Check your connection.");
  }
}

// Selects a unit in the dropdown. If the unit was removed from config/units.json
// but a product still uses it, it is added as an extra option so it isn't lost.
function setUnit(unit) {
  unitSelect.querySelectorAll("option[data-removed]").forEach((option) => option.remove());
  const exists = [...unitSelect.options].some((option) => option.value === unit);
  if (!exists) {
    const option = new Option(`${unit} (removed from list)`, unit);
    option.dataset.removed = "true";
    unitSelect.add(option);
  }
  unitSelect.value = unit;
}

// Opens the popup empty (add) or filled in with a product (edit).
function openForm(product) {
  editingId = product ? product.id : null;
  modalTitle.textContent = product ? "Edit product" : "Add product";
  nameInput.value = product ? product.name : "";
  priceInput.value = product ? priceForInput(product.price) : "";
  setUnit(product ? product.unit : unitSelect.options[0].value);
  hideError("product-form-error");
  modal.show();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError("product-form-error");

  const name = nameInput.value.trim();
  const price = parsePrice(priceInput.value);
  if (!name) {
    showError("product-form-error", "Name is required.");
    nameInput.focus();
    return;
  }
  if (price === null || price <= 0) {
    showError("product-form-error", "Enter a price like 12 or 12.50.");
    priceInput.focus();
    return;
  }

  saveButton.disabled = true;
  try {
    const url = editingId ? `/api/products/${editingId}` : "/api/products";
    const response = await apiFetch(url, {
      method: editingId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, price, unit: unitSelect.value }),
    });
    if (!response) return;
    const data = await response.json();
    if (!response.ok) {
      showError("product-form-error", data.error || "Could not save the product.");
      return;
    }
    modal.hide();
    await loadProducts();
  } catch {
    showError("product-form-error", "Cannot reach the server. Check your connection.");
  } finally {
    saveButton.disabled = false;
  }
});

// --- Import from CSV ---------------------------------------------------------

const importModalElement = document.getElementById("import-modal");
const importModal = bootstrap.Modal.getOrCreateInstance(importModalElement);
const importFile = document.getElementById("import-file");
const importErrors = document.getElementById("import-errors");
const importButton = document.getElementById("import-button");

function showImportErrors(errors, total) {
  const list = document.createElement("ul");
  list.className = "mb-0 ps-3";
  for (const error of errors) {
    const li = document.createElement("li");
    li.textContent = error;
    list.append(li);
  }
  const title = document.createElement("div");
  title.className = "fw-semibold mb-1";
  title.textContent = "Nothing was imported. Fix these rows and try again:";
  importErrors.replaceChildren(title, list);
  if (total > errors.length) {
    const more = document.createElement("div");
    more.textContent = `…and ${total - errors.length} more.`;
    importErrors.append(more);
  }
  importErrors.classList.remove("d-none");
}

importModalElement.addEventListener("show.bs.modal", () => {
  importFile.value = "";
  importErrors.classList.add("d-none");
});

document.getElementById("import-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  importErrors.classList.add("d-none");
  if (!importFile.files.length) {
    showImportErrors(["Choose a CSV file."], 1);
    return;
  }

  const body = new FormData();
  body.append("file", importFile.files[0]);
  importButton.disabled = true;
  try {
    const response = await apiFetch("/api/products/import", { method: "POST", body });
    if (!response) return;
    if (response.status === 413) {
      showImportErrors(["The file is too big (max 2 MB)."], 1);
      return;
    }
    const data = await response.json();
    if (!response.ok) {
      showImportErrors(data.errors || ["Could not import the file."], data.error_count || 1);
      return;
    }
    importModal.hide();
    document.getElementById("import-message-text").textContent =
      `Import done: ${data.added} added, ${data.updated} price updated, ${data.unchanged} unchanged.`;
    document.getElementById("import-message").classList.remove("d-none");
    await loadProducts();
  } catch (error) {
    console.error(error);
    showImportErrors(["Cannot reach the server. Check your connection."], 1);
  } finally {
    importButton.disabled = false;
  }
});

document.getElementById("add-product-button").addEventListener("click", () => openForm(null));
modalElement.addEventListener("shown.bs.modal", () => nameInput.focus());
searchInput.addEventListener("input", render);

loadProducts();
