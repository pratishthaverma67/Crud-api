"""
Task API - now backed by SQLite instead of an in-memory list.

WHAT CHANGED FROM ASSIGNMENT 1:
- The global `tasks = [...]` Python list is GONE. Data now lives in a
  file called tasks.db, so it survives server restarts.
- Every endpoint that used to loop over the `tasks` list now opens a
  connection to tasks.db and runs an SQL query instead.
- We added `init_db()`, which runs once when the server starts. It
  creates the `tasks` table if it doesn't exist yet, and inserts the
  3 sample tasks ONLY if the table is currently empty (so restarting
  the server never duplicates them).
- The API endpoints, request bodies, response shapes, status codes,
  and validation rules (400 / 404) are all unchanged.
"""

import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# ---------------------------------------------------------------------
# 1. Basic setup
# ---------------------------------------------------------------------

DB_NAME = "tasks.db"  # this file will appear in your project folder

app = FastAPI(
    title="Task API",
    description="A tiny CRUD API for managing a SQLite-backed to-do list.",
    version="2.0"
)


# ---------------------------------------------------------------------
# 2. Database helper functions
# ---------------------------------------------------------------------

def get_db_connection():
    """
    Opens a new connection to the SQLite database file.

    We open a fresh connection for every request instead of sharing one
    global connection. This is the simplest, safest pattern for a small
    beginner project and avoids threading issues (FastAPI can handle
    multiple requests concurrently).
    """
    conn = sqlite3.connect(DB_NAME)
    # row_factory lets us access columns by name (row["title"]) instead
    # of by position (row[1]), which makes the code much more readable.
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Runs once when the app starts.
    - Creates the `tasks` table if it doesn't already exist.
    - If the table is EMPTY, inserts the 3 sample tasks.
    - If the table already has data (e.g. after a restart), does nothing,
      so we never get duplicate sample rows.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS = safe to run every startup.
    # done is stored as INTEGER (0 = False, 1 = True) because SQLite
    # has no native boolean type, but "BOOLEAN" is a valid SQLite type
    # alias for INTEGER, so we can label it that way for clarity.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    # Check how many rows already exist.
    cursor.execute("SELECT COUNT(*) FROM tasks")
    row_count = cursor.fetchone()[0]

    # Only seed sample data the very first time (empty table).
    if row_count == 0:
        sample_tasks = [
            ("Buy groceries", False),
            ("Finish assignment", False),
            ("Read a chapter", True),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            sample_tasks
        )

    conn.commit()
    conn.close()


# Run the DB setup once, as soon as the module loads / app starts.
@app.on_event("startup")
def on_startup():
    init_db()


def row_to_dict(row: sqlite3.Row) -> dict:
    """
    Converts a database row into a plain dict that matches the exact
    JSON shape the old in-memory version returned, e.g.:
    {"id": 1, "title": "Buy groceries", "done": False}
    """
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),  # convert SQLite's 0/1 back to True/False
    }


# ---------------------------------------------------------------------
# 3. Pydantic models (request body validation) - unchanged from before
# ---------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------
# 4. Simple, non-DB endpoints - unchanged from before
# ---------------------------------------------------------------------

@app.get("/", description="Basic info about this API")
def read_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health", description="Health check - confirms the server is alive")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------
# 5. CRUD endpoints - now talk to SQLite instead of the Python list
# ---------------------------------------------------------------------

@app.get("/tasks", description="List all tasks")
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL for "list all tasks" = SELECT * FROM tasks
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()

    # Convert every row into the same dict shape the old list used.
    return [row_to_dict(row) for row in rows]


@app.get("/tasks/{task_id}", description="Get a single task by id")
def get_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL for "get one task" = SELECT * FROM tasks WHERE id = ?
    # The "?" is a placeholder - sqlite3 safely substitutes task_id
    # for us, which prevents SQL injection.
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return row_to_dict(row)


@app.post("/tasks", status_code=201, description="Create a new task")
def create_task(new_task: TaskCreate):
    # Same validation rule as before: title can't be empty/whitespace.
    if not new_task.title or not new_task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL for "create a task" = INSERT INTO tasks (title, done) VALUES (?, ?)
    # We don't insert an id ourselves - SQLite's AUTOINCREMENT handles
    # generating the next id automatically (this replaces the old
    # `max(...) + 1` logic from the in-memory version).
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (new_task.title, False)
    )
    conn.commit()

    new_id = cursor.lastrowid  # the id SQLite just generated

    # Fetch the row we just inserted so we return the exact same
    # shape as before ({"id": ..., "title": ..., "done": ...}).
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_dict(row)


@app.put("/tasks/{task_id}", description="Update a task's title and/or done status")
def update_task(task_id: int, updates: TaskUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # First, check the task exists (same 404 behavior as before).
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Work out the new values: use the provided update if given,
    # otherwise keep whatever is already in the database.
    new_title = existing["title"]
    if updates.title is not None:
        if not updates.title.strip():
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        new_title = updates.title

    new_done = existing["done"]
    if updates.done is not None:
        new_done = updates.done

    # SQL for "update a task" = UPDATE tasks SET title = ?, done = ? WHERE id = ?
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id)
    )
    conn.commit()

    # Fetch the updated row so the response reflects the final state.
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_dict(row)


@app.delete("/tasks/{task_id}", status_code=204, description="Delete a task by id")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL for "delete a task" = DELETE FROM tasks WHERE id = ?
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

    # cursor.rowcount tells us how many rows were actually deleted.
    # If it's 0, no task with that id existed -> 404.
    deleted_count = cursor.rowcount
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # 204 No Content responses must not return a body, so we return nothing.
    return


# ---------------------------------------------------------------------
# 6. Run the server directly with `python main.py`
# ---------------------------------------------------------------------
# FastAPI still needs an ASGI server to actually listen for HTTP requests
# - uvicorn is that server. This block just lets you start it by running
# `python main.py`, instead of typing the `uvicorn main:app --reload`
# command yourself every time.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)