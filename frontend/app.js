/* =========================================================
   Config
   ========================================================= */
// Point this at your running backend (see main.py CORS settings).
const API_BASE_URL = "http://127.0.0.1:8000";

// The FastAPI backend requires every task to belong to a project
// (tasks.project_id is a NOT NULL foreign key). Create one project
// via POST /projects (or the Swagger docs at /docs) and put its real
// id here.
const DEFAULT_PROJECT_ID = 1;

const STORAGE_KEY = "taskflow_tasks";

/* =========================================================
   State
   ========================================================= */
let tasks = [];
let nextLocalId = -1; // negative ids mark tasks created while offline

/* =========================================================
   DOM references
   ========================================================= */
const form = document.getElementById("add-task-form");
const titleInput = document.getElementById("task-title");
const dueDateInput = document.getElementById("task-due-date");
const priorityInput = document.getElementById("task-priority");
const titleError = document.getElementById("title-error");
const taskListEl = document.getElementById("task-list");
const taskCountEl = document.getElementById("task-count");
const emptyStateEl = document.getElementById("empty-state");
const addButton = form.querySelector(".btn-add");

/* =========================================================
   Init
   ========================================================= */
function init() {
  // Requirement 14: render the cached copy immediately so the page
  // never shows a blank list while the live request is in flight.
  tasks = loadFromCache();
  render();

  fetchTasksFromServer();

  form.addEventListener("submit", handleAddTask);
  titleInput.addEventListener("input", clearTitleErrorIfValid);
}

/* =========================================================
   localStorage cache
   ========================================================= */
function loadFromCache() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.error("Could not read cached tasks:", err);
    return [];
  }
}

function saveToCache() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  } catch (err) {
    console.error("Could not cache tasks:", err);
  }
}

/* =========================================================
   Backend sync
   ========================================================= */
async function fetchTasksFromServer() {
  try {
    const res = await fetch(`${API_BASE_URL}/tasks`);
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    tasks = await res.json();
    saveToCache();
    render();
  } catch (err) {
    // Backend unreachable — stay on the cached copy instead of blanking the page.
    console.warn("Backend not reachable, showing cached tasks:", err.message);
  }
}

/* =========================================================
   Validation
   ========================================================= */
function clearTitleErrorIfValid() {
  if (titleInput.value.trim() !== "") {
    titleError.textContent = "";
  }
}

/* =========================================================
   Add task
   ========================================================= */
async function handleAddTask(event) {
  event.preventDefault(); // Requirement 12: never let the form actually submit/reload

  const title = titleInput.value.trim();
  if (title === "") {
    titleError.textContent = "Task title cannot be empty.";
    titleInput.focus();
    return;
  }
  titleError.textContent = "";

  const newTaskPayload = {
    title: title,
    priority: priorityInput.value,
    due_date: dueDateInput.value.trim() || null,
    status: "pending",
    project_id: DEFAULT_PROJECT_ID,
  };

  addButton.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newTaskPayload),
    });
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const savedTask = await res.json();
    tasks.push(savedTask);
  } catch (err) {
    console.warn("Could not save to backend, saving locally only:", err.message);
    tasks.push({ id: nextLocalId--, ...newTaskPayload, _unsynced: true });
  }

  saveToCache();
  render();

  form.reset();
  priorityInput.value = "medium";
  titleInput.focus();
  addButton.disabled = false;
}

/* =========================================================
   Delete task
   ========================================================= */
async function handleDeleteTask(taskId) {
  const task = tasks.find((t) => t.id === taskId);
  if (!task) return;

  // Only hit the backend for tasks that actually exist there (positive ids).
  if (taskId > 0) {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
    } catch (err) {
      console.warn("Could not delete on backend, removing locally only:", err.message);
    }
  }

  tasks = tasks.filter((t) => t.id !== taskId);
  saveToCache();
  render();
}

/* =========================================================
   Edit task (inline)
   ========================================================= */
function handleEditTask(taskId) {
  const itemEl = taskListEl.querySelector(`[data-task-id="${taskId}"]`);
  const task = tasks.find((t) => t.id === taskId);
  if (!itemEl || !task) return;
  itemEl.replaceWith(createEditForm(task));
}

async function saveEditedTask(taskId, updatedFields) {
  if (!updatedFields.title || updatedFields.title.trim() === "") {
    return false; // caller shows the inline error
  }
  updatedFields.title = updatedFields.title.trim();

  if (taskId > 0) {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedFields),
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const savedTask = await res.json();
      tasks = tasks.map((t) => (t.id === taskId ? savedTask : t));
    } catch (err) {
      console.warn("Could not update on backend, updating locally only:", err.message);
      tasks = tasks.map((t) => (t.id === taskId ? { ...t, ...updatedFields } : t));
    }
  } else {
    tasks = tasks.map((t) => (t.id === taskId ? { ...t, ...updatedFields } : t));
  }

  saveToCache();
  render();
  return true;
}

/* =========================================================
   Rendering (DOM API only — no innerHTML with user data)
   ========================================================= */
function render() {
  // Clear the container without ever touching innerHTML.
  while (taskListEl.firstChild) {
    taskListEl.removeChild(taskListEl.firstChild);
  }

  if (tasks.length === 0) {
    emptyStateEl.hidden = false;
  } else {
    emptyStateEl.hidden = true;
    tasks.forEach((task) => {
      taskListEl.appendChild(createTaskElement(task));
    });
  }

  taskCountEl.textContent = `${tasks.length} task${tasks.length === 1 ? "" : "s"}`;
}

function createTaskElement(task) {
  const item = document.createElement("div");
  item.className = `task-item priority-${task.priority}`;
  item.dataset.taskId = task.id;

  const main = document.createElement("div");
  main.className = "task-main";

  const title = document.createElement("h3");
  title.className = "task-title";
  title.textContent = task.title; // textContent — safe against markup/scripts in user input

  const actions = document.createElement("div");
  actions.className = "task-actions";

  const editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.className = "btn-icon btn-edit";
  editBtn.textContent = "Edit";
  editBtn.addEventListener("click", () => handleEditTask(task.id));

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "btn-icon btn-delete";
  deleteBtn.textContent = "Delete";
  deleteBtn.addEventListener("click", () => handleDeleteTask(task.id));

  actions.appendChild(editBtn);
  actions.appendChild(deleteBtn);
  main.appendChild(title);
  main.appendChild(actions);

  const meta = document.createElement("div");
  meta.className = "task-meta";

  const dueSpan = document.createElement("span");
  dueSpan.className = "task-due";
  dueSpan.textContent = task.due_date ? `Due: ${task.due_date}` : "No due date";

  const priorityBadge = document.createElement("span");
  priorityBadge.className = `task-priority-badge priority-${task.priority}`;
  priorityBadge.textContent = task.priority;

  meta.appendChild(dueSpan);
  meta.appendChild(priorityBadge);

  item.appendChild(main);
  item.appendChild(meta);

  return item;
}

function createEditForm(task) {
  const wrapper = document.createElement("div");
  wrapper.className = "task-item editing";
  wrapper.dataset.taskId = task.id;

  const editRow = document.createElement("div");
  editRow.className = "edit-row";

  const titleField = document.createElement("input");
  titleField.type = "text";
  titleField.value = task.title;
  titleField.setAttribute("aria-label", "Task title");

  const dueField = document.createElement("input");
  dueField.type = "text";
  dueField.value = task.due_date || "";
  dueField.placeholder = "Due date";
  dueField.setAttribute("aria-label", "Due date");

  const priorityField = document.createElement("select");
  priorityField.setAttribute("aria-label", "Priority");
  ["low", "medium", "high"].forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
    if (p === task.priority) opt.selected = true;
    priorityField.appendChild(opt);
  });

  editRow.appendChild(titleField);
  editRow.appendChild(dueField);
  editRow.appendChild(priorityField);

  const editError = document.createElement("span");
  editError.className = "field-error";

  const actions = document.createElement("div");
  actions.className = "task-actions";

  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "btn-icon btn-save";
  saveBtn.textContent = "Save";
  saveBtn.addEventListener("click", async () => {
    const success = await saveEditedTask(task.id, {
      title: titleField.value,
      due_date: dueField.value.trim() || null,
      priority: priorityField.value,
    });
    if (!success) {
      editError.textContent = "Task title cannot be empty.";
    }
  });

  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "btn-icon btn-cancel";
  cancelBtn.textContent = "Cancel";
  cancelBtn.addEventListener("click", () => render());

  actions.appendChild(saveBtn);
  actions.appendChild(cancelBtn);

  wrapper.appendChild(editRow);
  wrapper.appendChild(editError);
  wrapper.appendChild(actions);

  return wrapper;
}

init();