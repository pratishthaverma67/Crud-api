# FastAPI CRUD API

A simple CRUD (Create, Read, Update, Delete) REST API built using **FastAPI**. This project stores data in memory and does not use a database.

## Features

- Create a new task
- Retrieve all tasks
- Retrieve a task by ID
- Update an existing task
- Delete a task
- Interactive API documentation with Swagger UI

## Tech Stack

- Python 3.x
- FastAPI
- Uvicorn
- Pydantic

## Project Structure

```
.
├── main.py
├── README.md
└── .gitignore
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repository.git
```

### 2. Navigate to the project directory

```bash
cd your-repository
```

### 3. Create a virtual environment (Optional but Recommended)

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install fastapi uvicorn
```

## Running the Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically generates interactive API documentation.

- Swagger UI:
  ```
  http://127.0.0.1:8000/docs
  ```

- ReDoc:
  ```
  http://127.0.0.1:8000/redoc
  ```

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | Get all tasks |
| GET | `/tasks/{task_id}` | Get a task by ID |
| POST | `/tasks` | Create a new task |
| PUT | `/tasks/{task_id}` | Update an existing task |
| DELETE | `/tasks/{task_id}` | Delete a task |

## Example Task Object

```json
{
  "id": 1,
  "title": "Buy groceries",
  "done": false
}
```

## Notes

- This project uses an **in-memory list** to store tasks.
- Data is **not persistent** and will reset whenever the server restarts.
- No external database is required.

## Future Improvements

- SQLite/PostgreSQL integration
- User authentication
- Pagination
- Search and filtering
- Docker support
- Unit testing

## License

This project is created for learning and educational purposes.