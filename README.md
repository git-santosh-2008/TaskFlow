# TaskFlow

A modular FastAPI backend for managing **Users → Projects → Tasks**, built with
SQLAlchemy ORM, Pydantic validation, custom middleware, and CORS support.

---

## 1. Project Structure

```
backend/
│
├── requirements.txt     # Python dependencies
├── database.py          # SQLAlchemy engine & session setup
├── models.py             # SQLAlchemy ORM models (User, Project, Task)
├── schemas.py             # Pydantic request/response schemas & validators
├── dependencies.py       # Shared FastAPI dependencies (get_db)
├── middleware.py         # Custom request-logging middleware
│
├── routers/               # API route handlers (one file per resource)
│   ├── __init__.py
│   ├── users.py
│   ├── projects.py
│   └── tasks.py
│
└── main.py                # Application entry point — wires everything together
```

Each concern lives in its own file so routes, models, schemas, and shared
logic can be edited independently without touching unrelated code.

---

## 2. Setup & Run (Quick — local SQLite, zero config)

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server (auto-reload on code changes)
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive Swagger docs: `http://127.0.0.1:8000/docs`

By default (no `.env` file) a local SQLite file `taskflow.db` is created
automatically on first run — no separate database setup needed. Follow
Section 2A below if you want to use Supabase (Postgres) instead.

---

## 2A. Running on Your Own Laptop with Supabase (VS Code, step-by-step)

This is the **only place you need to change anything** — nothing else in
the code needs editing to switch databases.

**Step 1 — Open the project in VS Code**
- `File -> Open Folder` -> select the `taskflow_backend` folder.
- Make sure the VS Code integrated terminal's working directory is this
  folder (the one containing `main.py`).

**Step 2 — Create & activate a virtual environment** (in the VS Code terminal)
```bash
python3 -m venv venv
source venv/bin/activate        # Windows (PowerShell): venv\Scripts\Activate.ps1
```
VS Code may prompt "Select Interpreter" — pick the one inside `venv/`.

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Get your Supabase connection string**
- Go to your project on [supabase.com](https://supabase.com) → **Project
  Settings** → **Database** → **Connection string** → **URI** tab.
- Copy the string. It looks like:
  `postgresql://postgres:[YOUR-PASSWORD]@db.abcdefgh.supabase.co:5432/postgres`
- Replace `[YOUR-PASSWORD]` with your actual database password (the one
  you set when creating the Supabase project — not your Supabase login
  password).

**Step 5 — Create your `.env` file (THIS is where the Supabase URL goes)**
- In VS Code, duplicate `.env.example` and rename the copy to `.env`
  (exactly `.env`, no `.example`), in the project root — same folder as
  `main.py`.
- Open `.env` and paste your real connection string as the value:
  ```
  DATABASE_URL=postgresql://postgres:your_actual_password@db.abcdefgh.supabase.co:5432/postgres
  ```
- Save the file. `database.py` already reads this automatically via
  `load_dotenv()` — you do **not** need to edit `database.py`,
  `models.py`, or any router file for this.
- `.env` is already listed in `.gitignore`, so your password won't
  accidentally get committed to git.

**Step 6 — Run the app**
```bash
uvicorn main:app --reload
```
On startup, `Base.metadata.create_all(bind=engine)` in `main.py` will
create the `users`, `projects`, and `tasks` tables directly inside your
Supabase Postgres database (visible under **Table Editor** in the
Supabase dashboard) instead of the local SQLite file.

**Step 7 (only if your frontend runs on a different port/origin)**
- If your frontend is NOT on `http://localhost:5500` or
  `http://127.0.0.1:5500`, open `main.py` and edit the `allow_origins`
  list inside `app.add_middleware(CORSMiddleware, ...)` to add your
  frontend's actual URL — this is the **only other line** you might need
  to touch on your laptop.

**What you never need to edit:** `models.py`, `schemas.py`,
`dependencies.py`, `middleware.py`, or anything in `routers/` — none of
that is environment-specific.

---



## 3. Database Schema

Three related tables, wired with foreign keys and constraints:

| Table      | Column       | Type    | Constraints                                  |
|------------|--------------|---------|-----------------------------------------------|
| `users`    | `id`         | Integer | Primary Key                                   |
|            | `name`       | String  | NOT NULL                                      |
|            | `email`      | String  | NOT NULL, UNIQUE                              |
| `projects` | `id`         | Integer | Primary Key                                   |
|            | `title`      | String  | NOT NULL                                      |
|            | `owner_id`   | Integer | NOT NULL, Foreign Key → `users.id`            |
| `tasks`    | `id`         | Integer | Primary Key                                   |
|            | `title`      | String  | NOT NULL                                      |
|            | `priority`   | String  | NOT NULL, CHECK IN ('low','medium','high')    |
|            | `due_date`   | String  | Nullable — raw text (manual date or AI phrase like "next friday") |
|            | `status`     | String  | Default `"pending"`                           |
|            | `project_id` | Integer | NOT NULL, Foreign Key → `projects.id`         |

**Relationships** (SQLAlchemy `relationship()` with `back_populates` on both sides):
- `User.projects` ↔ `Project.owner`
- `Project.tasks` ↔ `Task.project`

This means `a_project.tasks` and `a_task.project` both resolve directly through
the ORM without extra queries.

`priority` is restricted to `"low" | "medium" | "high"` at **two layers**:
a Pydantic `Field(pattern=...)` in `schemas.py` (rejects bad input with `422`
before it touches the DB), and a `CheckConstraint` in `models.py` (enforced
by the database itself as a safety net).

---

## 4. API Endpoints

### Users
| Method | Path      | Status | Description         |
|--------|-----------|--------|----------------------|
| POST   | `/users`  | 201    | Create a user        |
| GET    | `/users`  | 200    | List all users       |

### Projects
| Method | Path                   | Status | Description                          |
|--------|------------------------|--------|----------------------------------------|
| POST   | `/projects`            | 201    | Create a project (404 if owner missing) |
| GET    | `/projects`            | 200    | List all projects                     |
| GET    | `/projects/statistics` | 200    | Per-project task count & status breakdown (SQL `COUNT` + `GROUP BY`, computed in the query — not in Python) |

### Tasks
| Method | Path            | Status | Description                        |
|--------|-----------------|--------|--------------------------------------|
| POST   | `/tasks`        | 201    | Create a task (404 if project missing) |
| GET    | `/tasks`        | 200    | List all tasks                       |
| GET    | `/tasks/{id}`   | 200    | Get one task (404 if not found)      |
| PUT    | `/tasks/{id}`   | 200    | Update a task (404 if not found)     |
| DELETE | `/tasks/{id}`   | 200    | Delete a task (404 if not found)     |

Sending an invalid body to any `POST`/`PUT` (e.g. a blank title, or a
`priority` outside `low`/`medium`/`high`) returns **422 Unprocessable Entity**
automatically, via Pydantic validation.

---

## 5. Example Requests

```bash
# Create a user
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Aman", "email": "aman@example.com"}'

# Create a project (owner_id must exist)
curl -X POST http://127.0.0.1:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"title": "Website Revamp", "owner_id": 1}'

# Create a task
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Design homepage", "priority": "high", "due_date": "next friday", "project_id": 1}'

# Get task statistics per project
curl http://127.0.0.1:8000/projects/statistics
```

---

## 6. Cross-Cutting Features

- **Shared DB dependency (`dependencies.py::get_db`)** — one `Depends(get_db)`
  function, reused across every route in `users.py`, `projects.py`, and
  `tasks.py` — no duplicated session-management logic.
- **Request logging middleware (`middleware.py::log_requests`)** — runs on
  every request, logs HTTP method, path, and processing time in milliseconds
  to the console.
- **CORS (`main.py`)** — explicitly allows `http://localhost:5500` and
  `http://127.0.0.1:5500`, with `GET/POST/PUT/DELETE/PATCH` methods and
  `Content-Type`/`Authorization` headers listed explicitly (no wildcard
  defaults).

---

## 7. Notes

- `taskflow.db` is created in the project root the first time the app runs;
  delete it to reset all data.
- Tables are created automatically at startup via
  `Base.metadata.create_all(bind=engine)` — no separate migration step needed
  for this project's scope.





  # TaskFlow Frontend


Plain HTML/CSS/JS frontend for the TaskFlow backend — no build step, no
framework.

## Files
- `index.html` — semantic structure: header, add-task form, task list container
- `style.css` — box-model styling, sticky header, two responsive breakpoints
- `app.js` — all DOM rendering + CRUD logic + localStorage caching

## Before running

1. **Start the backend first** (`uvicorn main:app --reload` from the `backend/`
   folder) — this frontend talks to it over `fetch()`.

2. **Create at least one project** so tasks have somewhere to attach to.
   Easiest way: open `http://127.0.0.1:8000/docs` (Swagger UI) → `POST /users`
   → `POST /projects` (using that user's id as `owner_id`) → note the
   `id` the response gives you for the project.

3. **Open `script.js`** and set that id here:
   ```js
   const DEFAULT_PROJECT_ID = 1; // <- change to your real project id
   ```
   This is the only line you need to edit to connect the frontend to your
   own backend data.

## Running the frontend

Don't open `index.html` directly by double-clicking it (fetch calls behave
oddly on the `file://` protocol). Serve it instead:

- **VS Code**: install the "Live Server" extension → right-click
  `index.html` → "Open with Live Server". By default this runs on
  `http://127.0.0.1:5500`, which matches the backend's CORS whitelist.
- Or any static server, e.g. `python3 -m http.server 5500`.

If your frontend ends up on a different port, add that origin to
`allow_origins` in the backend's `main.py` CORS config.

## Behavior notes

- On page load, the task list renders instantly from whatever was cached
  in `localStorage` last time, then quietly refreshes from the live
  backend — so the page never shows a blank list while loading.
- If the backend is unreachable, add/edit/delete still work locally
  (changes are cached but marked unsynced) so you can keep testing the UI
  without the server running.

