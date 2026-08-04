# TaskFlow

A full-stack task manager built as a learning/assessment project:
- **Backend** — FastAPI + SQLAlchemy REST API, backed by SQLite (default) or
  Supabase/Postgres
- **Frontend** — plain HTML/CSS/JS, no framework, no build step, talks to the
  backend live over the Fetch API (no mock data anywhere)

```
taskflow/
├── README.md          ← you are here
├── backend/
│   ├── main.py             — app entry point, CORS, middleware, routers
│   ├── database.py          — SQLAlchemy engine/session, reads DATABASE_URL
│   ├── models.py             — User, Project, Task ORM models
│   ├── schemas.py             — Pydantic request/response models + validators
│   ├── dependencies.py         — shared get_db() dependency
│   ├── middleware.py            — request logging middleware
│   ├── routers/
│   │   ├── users.py
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── requirements.txt
│   ├── .env.example              — template for your Supabase connection string
│   └── .gitignore
└── frontend/
    ├── index.html         — header, add-task form, task list container
    ├── styles.css          — box-model styling, sticky header, 2 breakpoints
    └── script.js            — rendering, CRUD, validation, localStorage cache
```

---

## 1. Database Schema

Three related tables:

| Table      | Column       | Type    | Constraints                                |
|------------|--------------|---------|---------------------------------------------|
| `users`    | `id`         | Integer | Primary Key                                 |
|            | `name`       | String  | NOT NULL                                    |
|            | `email`      | String  | NOT NULL, UNIQUE                            |
| `projects` | `id`         | Integer | Primary Key                                 |
|            | `title`      | String  | NOT NULL                                    |
|            | `owner_id`   | Integer | NOT NULL, Foreign Key → `users.id`          |
| `tasks`    | `id`         | Integer | Primary Key                                 |
|            | `title`      | String  | NOT NULL                                    |
|            | `priority`   | String  | NOT NULL, CHECK IN ('low','medium','high')  |
|            | `due_date`   | String  | Nullable — raw text (manual date or phrase like "next friday") |
|            | `status`     | String  | Default `"pending"`                         |
|            | `project_id` | Integer | NOT NULL, Foreign Key → `projects.id`       |

Relationships (`relationship()` with `back_populates` on both sides):
`User.projects` ↔ `Project.owner`, and `Project.tasks` ↔ `Task.project`.

---

## 2. How to run the whole app locally (Two-process run)

This is the **only supported way** to run this project — one terminal for
the backend, one for the frontend. Follow in order, from a fresh clone.

### Terminal 1 — Backend (port 8000)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

You should see `Uvicorn running on http://127.0.0.1:8000`. Leave this
terminal running.

By default this uses a local SQLite file (`taskflow.db`) — zero setup
needed. **To use Supabase instead**, see Section 3 below.

### Terminal 2 — Frontend (port 5500)

Open a **second, new** terminal (don't close Terminal 1):

```bash
cd frontend
python3 -m http.server 5500
```

(Or in VS Code: right-click `frontend/index.html` → "Open with Live
Server" — also defaults to port 5500.)

### Open the app

Go to **`http://127.0.0.1:5500`** in your browser — not `:8000`, that's the
backend's raw JSON API, not the UI. Interactive API docs (Swagger) live at
`http://127.0.0.1:8000/docs`.

### One-time setup: create a project

`tasks.project_id` is a required foreign key, so create one project before
adding tasks in the UI:

1. Open `http://127.0.0.1:8000/docs`.
2. Run `POST /users` with any name/email → note the returned `id`.
3. Run `POST /projects` using that `id` as `owner_id` → note the returned
   project `id`.
4. Open `frontend/script.js`, find this line near the top, and set it to
   that project id:
   ```js
   const DEFAULT_PROJECT_ID = 1; // <- your real project id here
   ```
5. Refresh `http://127.0.0.1:5500`.

### Why the two ports must match

- `backend/main.py`'s CORS config explicitly allows only
  `http://localhost:5500` and `http://127.0.0.1:5500`.
- `frontend/script.js`'s `API_BASE_URL` points at `http://127.0.0.1:8000`.

Both are already set to match. If you serve the frontend on a different
port, update **both**: `allow_origins` in `backend/main.py`, and wherever
your static server actually runs.

---

## 3. Using Supabase (Postgres) instead of SQLite

No code needs editing for this — only a config file.

1. **Get your connection string**: Supabase Dashboard → your project →
   Project Settings → Database → Connection string → URI tab. It looks like:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
   ```
2. **Create `backend/.env`** (copy `backend/.env.example` and rename), and
   paste your string in as:
   ```
   DATABASE_URL=postgresql://postgres.xxxxx:your_actual_password@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
   ```
   Replace `[YOUR-PASSWORD]` with your real DB password — don't leave the
   brackets in, and don't leave stray `#` or extra `@` characters in the
   string (a common copy-paste mistake).
3. Restart the backend (`Ctrl+C`, then `uvicorn main:app --reload` again).
4. Confirm it worked: add a task from the frontend, then check
   **Supabase Dashboard → Table Editor → tasks** — the row should appear
   there.

`backend/.env` is already listed in `.gitignore`, so your password is never
committed to git.

---

## 4. API Endpoints

**Users** — `POST /users` (201), `GET /users` (200)

**Projects** — `POST /projects` (201, 404 if owner missing), `GET /projects`
(200), `GET /projects/statistics` (200 — per-project task count + status
breakdown via SQL `COUNT`+`GROUP BY`)

**Tasks** — `POST /tasks` (201, 404 if project missing), `GET /tasks` (200),
`GET /tasks/{id}` (200/404), `PUT /tasks/{id}` (200/404), `DELETE /tasks/{id}`
(200/404)

Invalid request bodies (blank title, priority outside low/medium/high)
return `422` automatically via Pydantic validation.

---

## 5. Troubleshooting

| Symptom (browser console) | What it means | Fix |
|---|---|---|
| `blocked by CORS policy` | Frontend is running on a port not in `allow_origins` | Serve the frontend on port `5500` (Live Server / `http.server 5500`) — don't open `index.html` directly via `file://` |
| `Failed to fetch` / `ERR_CONNECTION_REFUSED` | Backend isn't running | Start it: `cd backend && uvicorn main:app --reload` |
| `POST /tasks 404 (Not Found)` | `DEFAULT_PROJECT_ID` in `script.js` doesn't match a real project in the database | Create a project via `/docs` (Section 2, "One-time setup") and update the id in `script.js` |
| `POST /tasks 500` + backend terminal shows `psycopg2.OperationalError: server closed the connection unexpectedly` | Supabase connection dropped/paused | Check the project isn't paused in the Supabase dashboard; `backend/database.py` already sets `pool_pre_ping=True` and `pool_recycle=300` to auto-recover from this |
| `could not translate host name "...supabase.com"` | Malformed `DATABASE_URL` (stray `#`, extra `@`, or unencoded special character in the password) | Re-copy the connection string fresh from the Supabase dashboard into `backend/.env` |
| `Uncaught (in promise) Error: A listener indicated an asynchronous response...` | Unrelated to this app — caused by a Chrome extension (Grammarly, ad-blocker, etc.), not the code | Safe to ignore; confirm by opening the page in Incognito mode, where it won't appear |
| Random-looking port numbers in backend logs (e.g. `127.0.0.1:10887`) | Normal — each browser request uses a random local outgoing port | Ignore; the backend's actual server port is always the fixed `:8000` |

---

## 6. What's already handled (no need to re-check)

- CORS, request-logging middleware, and the shared `get_db()` dependency
  are wired once in `backend/main.py` / `backend/dependencies.py` and reused
  across every router.
- The frontend renders the task list via `document.createElement()` /
  `appendChild()` / `textContent` only — no `innerHTML` with user data.
- localStorage is a **cache only**: on load it renders instantly from the
  cached copy, then a live `fetch()` to the backend overwrites it — the
  page never shows a blank list while loading, but the backend/Supabase
  database is always the source of truth.

