# Productivity App - Notes API Backend

A RESTful Flask API backend built for a personal productivity application. It provides session-based user authentication and full CRUD capabilities for a user-owned productivity resource (Notes), featuring route protection, password hashing with Bcrypt, and pagination.

## Features

- **Authentication & Authorization**: Cookie and session-based authentication with `flask-bcrypt` for password hashing (`/signup`, `/login`, `/logout`, `/check_session`).
- **User-Owned Resource (Notes)**: Full CRUD endpoints for creating, reading, updating, and deleting notes with titles, content, categories, and timestamps.
- **Data Isolation**: Strict access controls ensuring users can only view, modify, or delete their own notes.
- **Pagination**: Resource index (`GET /notes`) supports `page` and `per_page` query parameters to paginate results efficiently.
- **Database Migrations & Seeding**: Database schema managed using Flask-Migrate with a comprehensive seed script populating demo users and notes via Faker.

---

## Tech Stack & Dependencies

- Python 3.8+
- Flask (2.2.2+)
- Flask-SQLAlchemy
- Flask-Migrate (Alembic)
- Flask-RESTful
- Flask-Bcrypt
- Flask-CORS
- Faker
- Pytest

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd flask-auth-notes-app
```

### 2. Install dependencies

Using **Pipenv**:
```bash
pipenv install
pipenv shell
```

Or using **venv & pip**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Apply database migrations
```bash
flask db upgrade
```

### 4. Seed sample data
Run the seed script to create demo users and sample notes:
```bash
python seed.py
```

> **Default Seed Credentials**:
> - **Username**: `demo_user` (or `alex_dev`, `sarah_m`, `jordan_t`)
> - **Password**: `password123`

---

## Running the Application

To run the Flask development server:
```bash
python app.py
```
Or:
```bash
flask run --port=5555
```

The API will be available at `http://localhost:5555`.

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required | Request Body Example | Success Status |
|---|---|---|---|---|---|
| `POST` | `/signup` | Registers a new user and logs them in | No | `{"username": "johndoe", "password": "securepassword"}` | `201 Created` |
| `POST` | `/login` | Authenticates an existing user and creates session | No | `{"username": "johndoe", "password": "securepassword"}` | `200 OK` |
| `DELETE` | `/logout` | Clears the session for the logged-in user | Yes | None | `200 OK` |
| `GET` | `/check_session` (or `/me`) | Returns the current logged-in user details | Yes | None | `200 OK` |

### Notes Endpoints

All notes endpoints require an active user session.

| Method | Endpoint | Description | Query Parameters | Request Body Example | Success Status |
|---|---|---|---|---|---|
| `GET` | `/notes` | Gets paginated list of notes owned by current user | `?page=1&per_page=5` | None | `200 OK` |
| `POST` | `/notes` | Creates a new note for current user | None | `{"title": "Meeting notes", "content": "Discussed roadmap", "category": "Work"}` | `201 Created` |
| `GET` | `/notes/<id>` | Retrieves a specific note by ID (must belong to current user) | None | None | `200 OK` |
| `PATCH` | `/notes/<id>` | Updates an existing note (must belong to current user) | None | `{"title": "Updated title", "content": "Updated content"}` | `200 OK` |
| `DELETE` | `/notes/<id>` | Deletes a note (must belong to current user) | None | None | `200 OK` |

### Example Response: `GET /notes?page=1&per_page=5`

```json
{
  "notes": [
    {
      "id": 1,
      "title": "Sprint Planning Notes",
      "content": "Discussed Q4 roadmap and planned backend auth deliverables with the team.",
      "category": "Work",
      "created_at": "2026-10-19T10:51:14.000000",
      "user_id": 1
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 5,
  "pages": 3
}
```

---

## Running Tests

Automated testing is configured using `pytest`. The test suite covers user registration, login, logout, session verification, note CRUD actions, pagination, error handling, and cross-user data isolation.

To run the tests:
```bash
pytest -v
```

All 13 test cases should pass.

---

## Project Structure

```text
flask-auth-notes-app/
├── app.py             # Flask application setup, routes, and RESTful resources
├── models.py          # SQLAlchemy User and Note models with password hashing
├── seed.py            # Database seeding script with Faker data
├── test_app.py        # Pytest test suite for auth and CRUD operations
├── migrations/        # Flask-Migrate Alembic version migrations
├── Pipfile            # Pipenv package specifications
├── requirements.txt   # Pinned pip requirements
├── instance/app.db    # SQLite development database
└── README.md          # Project documentation
```
