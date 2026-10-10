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
  price.textContent = formatAmount(product.price);

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

// Opens the popup empty (add) or filled in with a product (edit).
function openForm(product) {
  editingId = product ? product.id : null;
  modalTitle.textContent = product ? "Edit product" : "Add product";
  nameInput.value = product ? product.name : "";
  priceInput.value = product ? priceForInput(product.price) : "";
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
      body: JSON.stringify({ name, price }),
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

document.getElementById("add-product-button").addEventListener("click", () => openForm(null));
modalElement.addEventListener("shown.bs.modal", () => nameInput.focus());
searchInput.addEventListener("input", render);

loadProducts();
