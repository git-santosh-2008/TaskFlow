# TaskFlow

A full-stack task manager built as a learning/assessment project:
- **Backend** — FastAPI + SQLAlchemy REST API, backed by SQLite (default) or
  Supabase/Postgres
- **Frontend** — plain HTML/CSS/JS, no framework, no build step, talks to the
  backend live over the Fetch API (no mock data anywhere)

```
taskflow/
├── README.md          ← you are here (setup, endpoints, Section 2 write-up)
├── seed.py             — Section 2: benchmark seeding + comparison counts
├── check_algorithms.py  — Section 2: automated PASS/FAIL checks
├── results.txt            — Section 2: saved raw benchmark output (from seed.py)
├── backend/
│   ├── main.py             — app entry point, CORS, middleware, routers
│   ├── database.py          — SQLAlchemy engine/session, reads DATABASE_URL
│   ├── models.py             — User, Project, Task ORM models
│   ├── schemas.py             — Pydantic request/response models + validators
│   ├── dependencies.py         — shared get_db() dependency
│   ├── middleware.py            — request logging middleware
│   ├── algorithms.py             — Section 2: insertion_sort/binary_search/linear_search engine
│   ├── quick_add.py                — Section 3: mock parser + role-based prompt for /tasks/quick-add
│   ├── routers/
│   │   ├── users.py
│   │   ├── projects.py
│   │   └── tasks.py                — includes the Section 2 sort/search endpoints
│   ├── requirements.txt
│   └──── .env.example              — template for your Supabase connection string
├──── frontend/
│    ├── index.html         — header, add-task form, task list container
│    ├── style.css          — box-model styling, sticky header, 2 breakpoints
│    └── app.js            — rendering, CRUD, validation, localStorage cache
└── .gitignore
```

`seed.py` and `check_algorithms.py` live at the repo root (not inside
`backend/`) because they're standalone dev/verification tools, not part
of the running app — but they import the real engine straight out of
`backend/algorithms.py`, so they're always testing the exact same code
the API uses.

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
`GET /tasks?sort=priority|due_date` (200 — sorted via our own
`insertion_sort`, see Section 7), `GET /tasks/search?title=X&algo=binary|linear`
(200/404 — via our own `binary_search`/`linear_search`, see Section 7),
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

---

## 7. Assignment Section 2 — Sorting & Search Engine

`backend/algorithms.py` implements three hand-rolled functions —
`insertion_sort`, `binary_search`, `linear_search` — plus three
comparison-counting versions (`*_count`) used only by `seed.py`'s
benchmark below. **The API never calls Python's built-in
`sorted()`/`list.sort()`** — the two endpoints below are powered
entirely by these functions, operating on real rows fetched from the
database in the same request.

### New endpoints

| Method | Path                                          | Status | Description |
|--------|-----------------------------------------------|--------|--------------|
| GET    | `/tasks?sort=priority`                        | 200    | Tasks ordered by priority, sorted by our own `insertion_sort()` |
| GET    | `/tasks?sort=due_date`                        | 200    | Tasks ordered by due date, same engine |
| GET    | `/tasks/search?title=X&algo=binary\|linear`    | 200/404 | Exact-title lookup via our own `binary_search()`/`linear_search()` |

`GET /tasks/search` builds an in-memory `{"id","title"}` index from the
real `tasks` table; for `algo=binary` the index is sorted first with
`insertion_sort` and then searched with `binary_search`, for
`algo=linear` it's searched unsorted with `linear_search`.

Not-found convention: `binary_search`/`linear_search` return `None`
(not `-1`) when no match exists — chosen because it can never be
confused with a real index (index `0` is falsy but "found"), and reads
clearly in `if position is None:` checks.

### Time complexity

| Function        | Best case | Worst case | Why |
|------------------|-----------|------------|------|
| `insertion_sort` | O(n)      | O(n²)      | Best case: input already sorted, inner `while` never shifts. Worst case: input reverse-sorted, every new element shifts past all previous ones. |
| `binary_search`  | O(1)      | O(log n)   | Best case: target is the first element checked (the middle of the whole range). Worst case: target is absent, or found only after halving the range down to 1 element. |
| `linear_search`  | O(1)      | O(n)       | Best case: target is the very first element. Worst case: target is last, or absent — every element gets checked. |

### Benchmark results (Task 5)

Run from the **repo root**:
```bash
python3 seed.py
```
This generates synthetic task dicts (same `title`/`priority`/`due_date`
fields the real endpoints use) at three sizes, sorts/searches them with
the counting wrappers, prints the raw comparison counts, and saves them
to `results.txt`. Actual numbers from a real run:

```
--- n = 10 tasks ---
insertion_sort_count  (sort tasks by priority):              19 comparisons
insertion_sort_count  (sort search index by title):           9 comparisons
binary_search_count   (title present, mid element):           3 comparisons  (index=5)
binary_search_count   (title absent):                         4 comparisons  (index=None)
linear_search_count   (title present, mid element):           6 comparisons  (index=5)
linear_search_count   (title absent):                        10 comparisons  (index=None)

--- n = 500 tasks ---
insertion_sort_count  (sort tasks by priority):          42,913 comparisons
insertion_sort_count  (sort search index by title):         499 comparisons
binary_search_count   (title present, mid element):           8 comparisons  (index=250)
binary_search_count   (title absent):                         9 comparisons  (index=None)
linear_search_count   (title present, mid element):         251 comparisons  (index=250)
linear_search_count   (title absent):                       500 comparisons  (index=None)

--- n = 3000 tasks ---
insertion_sort_count  (sort tasks by priority):       1,543,975 comparisons
insertion_sort_count  (sort search index by title):       2,999 comparisons
binary_search_count   (title present, mid element):          11 comparisons  (index=1500)
binary_search_count   (title absent):                        12 comparisons  (index=None)
linear_search_count   (title present, mid element):       1,501 comparisons  (index=1500)
linear_search_count   (title absent):                     3,000 comparisons  (index=None)
```

Full output is also saved in `results.txt`.

### Is sorting first worth it? (Task 6)

The numbers above show two very different stories depending on the input
order. Sorting the search index by title cost only 9 / 499 / 2,999
comparisons at each size — essentially O(n) — because the synthetic
titles were generated in ascending order, so `insertion_sort`'s best
case kicked in. Sorting the *same-size* task list by priority (which is
randomly distributed, not pre-ordered) cost 19 / 42,913 / 1,543,975
comparisons — the O(n²) worst case, since ties and out-of-order values
force real shifting. This is the core trade-off: **`insertion_sort`'s
cost depends entirely on how sorted the input already is**, while
`binary_search` stayed cheap regardless (3 → 8 → 11 comparisons across a
300x size increase) because O(log n) barely grows.

Given how a team actually uses TaskFlow — listing/sorting tasks
repeatedly through the day, but adding or renaming tasks less often —
paying the sort cost on every `GET /tasks?sort=...` call is reasonable
at realistic team-sized task counts (tens to low hundreds), where even
the worst-case O(n²) sort finishes in well under a millisecond of real
work. It stops being worth it once a project's task list grows into the
thousands with frequent re-sorts, where the 1.5M-comparison worst case
becomes noticeable — at that scale, sorting once and reusing the sorted
order (or switching to an O(n log n) algorithm) pays off far more than
re-running `insertion_sort` on every list request. Binary search, by
contrast, is worth its one-time sorting cost at almost any scale a real
team would hit, since search happens far more often than the list is
restructured.

### Automated checks (Task 7)

Run from the **repo root**:
```bash
python3 check_algorithms.py
```
Prints a `PASS`/`FAIL` line for every required case (empty-list sort,
single-element sort, binary search at first/middle/last/absent, both
counting wrappers' return shapes). A real run currently prints 13
`PASS` lines and 0 `FAIL` lines.


### 8. Assignment Section 3 — AI Quick-Add

POST /tasks/quick-add creates a real task from one free-text sentence, in the same tasks table the rest of the app uses. Body:

json
{ "description": "Submit report urgent tomorrow", "project_id": 1 }
Parsing is done by mock_parse_task_description() in backend/quick_add.py — a deterministic, keyless, zero-network rule engine (the required baseline that's graded). It follows the exact keyword algorithm the assignment specifies, so any correct implementation produces identical output for the same input.
Prompt structure: build_parse_prompt() builds a standard role-based [{"role": "system", ...}, {"role": "user", ...}] message pair for every request — kept identical whether the mock or a real model ultimately answers it.
Optional real-LLM hook: gated behind the USE_REAL_LLM environment variable (default unset = off). The parse_task_description() dispatcher in quick_add.py is the single place this is decided: it only tries call_real_llm() (a minimal working example wired to the Anthropic API, imported only when actually called) when the flag is true AND a key is present, and falls back to the mock automatically on any failure or absence. It is never used during grading — the flag defaults off, and the endpoint works correctly with zero API keys in every configuration.
Validation: an unknown project_id returns 422 (not 404 — this endpoint deliberately differs from POST /tasks, per the Section 3 spec) with a Pydantic-shaped error. The parsed fields are also run through TaskCreate before any row is written; a failure there is also a 422 with no row created.
Which prompting technique this is modeled on

The system message in build_parse_prompt() is zero-shot: it states the extraction task and the exact decision rules directly ("high if 'urgent'/'asap' present, else low if...") without embedding any worked input→output example pairs inside the prompt itself. This was chosen over few-shot because the task is a closed, rule-based classification (3 priority values, a fixed list of date phrases) rather than an open-ended generation task — a model (or our mock) doesn't need example transcripts to infer the pattern when the rule itself is stated explicitly and unambiguously. This keeps token usage low and constant regardless of load, since a few-shot prompt would need several example description→JSON pairs added to every single request, multiplying cost per call with no accuracy benefit here. It isn't chain-of-thought either: the rules don't require multi-step reasoning to reach an answer, so asking a model to "think step by step" would only add latency and extra output tokens without improving reliability. For reliability, our mock enforces this zero-shot instruction as literal code — priority is always exactly one of three values and title is never empty — which is strictly more reliable than trusting a real model's free-text output; this is precisely why the mock, not a real LLM call, is what's graded.

Worked examples

Computed by actually running mock_parse_task_description() — not hand-calculated:

#	Input	Parsed output
1	"Call the client whenever you get a chance"	{"title": "Call the client you get a chance", "priority": "low", "due_date_hint": null}
2	"Submit invoice today, urgent!"	{"title": "Submit invoice , !", "priority": "high", "due_date_hint": "today"}
3	"Low priority: water the plants"	{"title": ": water the plants", "priority": "low", "due_date_hint": null}
4	"Team meeting next Monday to discuss urgent roadmap asap"	{"title": "Team meeting to discuss roadmap", "priority": "high", "due_date_hint": "next monday"}
5	"Plan the offsite next week if possible"	{"title": "Plan the offsite if possible", "priority": "medium", "due_date_hint": "next week"}

Try any input of your own via http://127.0.0.1:8000/docs → POST /tasks/quick-add, or independently re-run mock_parse_task_description("your text here") from a Python shell in backend/.