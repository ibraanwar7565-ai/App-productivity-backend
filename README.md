# Productivity App Backend (Notes)

A secure Flask REST API for a productivity app. Users sign up, log in, and manage
their own private **notes**. Authentication is **session-based** (cookies) with
bcrypt-hashed passwords, and note access is restricted so users can only see and
change their own data.

Built for the *Summative Lab: Full Auth Flask Backend – Productivity App*.

## Description

- **Auth:** signup, login, logout, and check-session using Flask sessions.
- **User model:** unique usernames, bcrypt-protected passwords (never readable).
- **Owned resource — Note:** each note belongs to a user and has `title`,
  `content`, `category`, and `created_at`.
- **Protected routes:** every `/notes` route requires a logged-in user, and a
  user can only access their own notes (others return 404).
- **Pagination:** the notes index supports `?page` and `?per_page` with metadata.

## Installation

```bash
pipenv install
pipenv shell
cd server
export FLASK_APP=app.py
export FLASK_RUN_PORT=5555

flask db init        # first time only
flask db migrate -m "initial migration"
flask db upgrade head
python seed.py
```

## Running

```bash
flask run
# or
python app.py
```

The provided **sessions** frontend client can point at this API.

## Testing

```bash
cd server
pytest
```

## Endpoints

### Auth
| Method | Path             | Description                                  |
|--------|------------------|----------------------------------------------|
| POST   | `/signup`        | Create a user, log them in (201 / 422)       |
| POST   | `/login`         | Log in (200 / 401)                           |
| DELETE | `/logout`        | Log out (204 / 401)                          |
| GET    | `/check_session` | Current user if logged in (200 / 401)        |

### Notes (auth required; user-owned)
| Method | Path                          | Description                               |
|--------|-------------------------------|-------------------------------------------|
| GET    | `/notes?page=&per_page=`      | Paginated list of the current user's notes |
| GET    | `/notes/<id>`                 | Get one of the user's notes (404 if not theirs) |
| POST   | `/notes`                      | Create a note (201 / 422)                 |
| PATCH  | `/notes/<id>`                 | Update a note                             |
| DELETE | `/notes/<id>`                 | Delete a note                             |

### Example

```bash
curl -c cookies.txt -X POST http://localhost:5555/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

curl -b cookies.txt -X POST http://localhost:5555/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "content": "2%", "category": "errands"}'

curl -b cookies.txt "http://localhost:5555/notes?page=1&per_page=5"
```

## Project structure

```
server/
├── app.py       # auth + notes routes
├── config.py    # app, db, migrate, bcrypt
├── models.py    # User, Note, schemas
├── seed.py      # example data
└── testing/
    └── test_app.py
```
