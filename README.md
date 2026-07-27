# Task API (SQLite version)

A tiny CRUD Task API built with FastAPI, now backed by a real SQLite
database (`tasks.db`) instead of an in-memory Python list.

## What changed from Assignment 1

| Assignment 1 | This version |
|---|---|
| `tasks = [...]` global list | `tasks.db` SQLite file |
| Data reset every restart | Data persists across restarts |
| Looped over the list with `for task in tasks` | Runs SQL queries (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) |
| `max(t["id"] ...) + 1` to generate ids | SQLite's `AUTOINCREMENT` generates ids |
| No SQL injection risk (no SQL at all) | Uses `?` placeholders in every query to stay injection-safe |

The API surface itself — endpoints, request bodies, response JSON shapes,
status codes (400/404/201/204) — is **unchanged**.

## Project files

```
task_api/
├── main.py               # the FastAPI app
├── requirements.txt      # Python dependencies
├── example_queries.sql   # sample SQL for manual testing
└── README.md             # this file
```

`tasks.db` will be created automatically the first time you run the app
— you don't need to create it yourself.

## Why SQLite?

SQLite was chosen because it needs no separate server or installation —
the entire database is just one file (`tasks.db`) sitting in the project
folder. That makes it perfect for a small learning project: you get real
persistence (data survives restarts) without the setup overhead of
running Postgres or MySQL. Python's built-in `sqlite3` module also means
zero extra dependencies for talking to the database.

## Where the database file lives

`tasks.db` is created automatically in the same folder as `main.py`, the
first time you run the app. You don't create it manually — `init_db()`
handles that on startup.

## Setup instructions

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate    # on Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Open the interactive API docs** in your browser:
   ```
   http://127.0.0.1:8000/docs
   ```

On the very first run, `tasks.db` is created in your project folder
and seeded with 3 sample tasks. On every future run, the app checks the
table first and will **not** re-insert those sample tasks — your real
data stays intact.

## Endpoints (unchanged from Assignment 1)

| Method | Path | Description | Success status |
|---|---|---|---|
| GET | `/` | Basic API info | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{id}` | Get one task | 200 (404 if missing) |
| POST | `/tasks` | Create a task | 201 (400 if title empty/missing) |
| PUT | `/tasks/{id}` | Update a task | 200 (404 if missing, 400 if title empty) |
| DELETE | `/tasks/{id}` | Delete a task | 204 (404 if missing) |

## SQL used, per endpoint

- `GET /tasks` → `SELECT * FROM tasks`
- `GET /tasks/{id}` → `SELECT * FROM tasks WHERE id = ?`
- `POST /tasks` → `INSERT INTO tasks (title, done) VALUES (?, ?)`
- `PUT /tasks/{id}` → `UPDATE tasks SET title = ?, done = ? WHERE id = ?`
- `DELETE /tasks/{id}` → `DELETE FROM tasks WHERE id = ?`

All values coming from the client are passed in using `?` placeholders
(never string-concatenated into the query), which is what protects the
app from SQL injection.

See `example_queries.sql` if you want to poke around the database
directly using the `sqlite3` command-line tool:

```bash
sqlite3 tasks.db
```

## Example SQL query I ran manually

Opened the database with the `sqlite3` command-line tool:

```bash
sqlite3 tasks.db
```

Then ran:

```sql
SELECT * FROM tasks WHERE done = 1;
```

Which returned only the tasks marked as completed, e.g.:

```
3|Read a chapter|1
```

This confirms the API and the raw database are in sync — anything you
change through `PUT /tasks/{id}` shows up immediately when you query the
table directly, and vice versa.

## Screenshot of database viewer

*(Add a screenshot here of `tasks.db` opened in DB Browser for SQLite,
or the output of `sqlite3 tasks.db` with `.tables` and `SELECT * FROM tasks;`
run in your terminal, as required by the assignment.)*

## Resetting the database

If you ever want to start fresh, just delete the `tasks.db` file and
restart the server — it will be recreated with the 3 sample tasks.

```bash
rm tasks.db
uvicorn main:app --reload
```
