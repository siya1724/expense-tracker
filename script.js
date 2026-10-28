// Personal Expense Tracker - frontend logic (vanilla JavaScript)

const API = "/api/expenses";

const form = document.getElementById("expense-form");
const formTitle = document.getElementById("form-title");
const formError = document.getElementById("form-error");
const idInput = document.getElementById("expense-id");
const amountInput = document.getElementById("amount");
const categoryInput = document.getElementById("category");
const dateInput = document.getElementById("date");
const descriptionInput = document.getElementById("description");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");

const filterCategory = document.getElementById("filter-category");
const filterMonth = document.getElementById("filter-month");
const clearFiltersBtn = document.getElementById("clear-filters");

const tbody = document.getElementById("expense-body");
const emptyMsg = document.getElementById("empty-msg");
const totalEl = document.getElementById("total");

let expenses = [];

function formatMoney(value) {
  return "₹" + Number(value).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function todayISO() {
  const d = new Date();
  const offset = d.getTimezoneOffset() * 60000;
  return new Date(d - offset).toISOString().slice(0, 10);
}

function showError(message) {
  formError.textContent = message;
  formError.classList.toggle("hidden", !message);
}

// ---------- Load data ----------

async function loadCategories() {
  const res = await fetch("/api/categories");
  const categories = await res.json();
  for (const name of categories) {
    categoryInput.add(new Option(name, name));
    filterCategory.add(new Option(name, name));
  }
}

async function loadExpenses() {
  const params = new URLSearchParams();
  if (filterCategory.value) params.set("category", filterCategory.value);
  if (filterMonth.value) params.set("month", filterMonth.value);

  const res = await fetch(API + "?" + params.toString());
  const data = await res.json();
  expenses = data.expenses;
  render(data.total);
}

// ---------- Render ----------

function render(total) {
  tbody.replaceChildren();

  for (const exp of expenses) {
    const tr = document.createElement("tr");

    const dateTd = document.createElement("td");
    dateTd.textContent = exp.date;

    const catTd = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = exp.category;
    catTd.appendChild(badge);

    const descTd = document.createElement("td");
    descTd.textContent = exp.description || "-";

    const amountTd = document.createElement("td");
    amountTd.className = "num";
    amountTd.textContent = formatMoney(exp.amount);

    const actionsTd = document.createElement("td");
    actionsTd.className = "actions";

    const editBtn = document.createElement("button");
    editBtn.className = "small secondary";
    editBtn.textContent = "Edit";
    editBtn.addEventListener("click", () => startEdit(exp));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "small danger";
    deleteBtn.textContent = "Delete";
    deleteBtn.addEventListener("click", () => deleteExpense(exp.id));

    actionsTd.append(editBtn, deleteBtn);
    tr.append(dateTd, catTd, descTd, amountTd, actionsTd);
    tbody.appendChild(tr);
  }

  emptyMsg.classList.toggle("hidden", expenses.length > 0);
  totalEl.textContent = formatMoney(total);
}

// ---------- Create / update ----------

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");

  const payload = {
    amount: amountInput.value,
    category: categoryInput.value,
    date: dateInput.value,
    description: descriptionInput.value,
  };

  const editingId = idInput.value;
  const url = editingId ? `${API}/${editingId}` : API;
  const method = editingId ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }
    resetForm();
    await loadExpenses();
  } catch (err) {
    showError("Could not reach the server. Is server.py running?");
  }
});

function startEdit(exp) {
  idInput.value = exp.id;
  amountInput.value = exp.amount;
  categoryInput.value = exp.category;
  dateInput.value = exp.date;
  descriptionInput.value = exp.description;

  formTitle.textContent = "Edit Expense";
  submitBtn.textContent = "Save Changes";
  cancelBtn.classList.remove("hidden");
  showError("");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  form.reset();
  idInput.value = "";
  dateInput.value = todayISO();
  formTitle.textContent = "Add Expense";
  submitBtn.textContent = "Add Expense";
  cancelBtn.classList.add("hidden");
  showError("");
}

cancelBtn.addEventListener("click", resetForm);

// ---------- Delete ----------

async function deleteExpense(id) {
  if (!confirm("Delete this expense?")) return;
  await fetch(`${API}/${id}`, { method: "DELETE" });
  if (idInput.value === String(id)) resetForm();
  await loadExpenses();
}

// ---------- Filters ----------

filterCategory.addEventListener("change", loadExpenses);
filterMonth.addEventListener("change", loadExpenses);
clearFiltersBtn.addEventListener("click", () => {
  filterCategory.value = "";
  filterMonth.value = "";
  loadExpenses();
});

// ---------- Start ----------

(async function init() {
  dateInput.value = todayISO();
  await loadCategories();
  await loadExpenses();
})();
