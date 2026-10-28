# Personal Expense Tracker

A beginner-friendly full-stack project: record, manage and track daily expenses.

**Tech stack:** HTML, CSS, JavaScript (frontend) · Python standard library `http.server` (backend) · SQLite (database). No Flask, no Chart.js, no pip installs.

## Features

- Add, view, edit and delete expenses (full CRUD)
- Category filter: Food, Travel, Shopping, Education, Bills, Other
- Monthly summary via month filter
- Total amount for whatever is currently shown
- SQLite storage (`expenses.db`), so data stays after you close the site

## How to run

1. Install Python 3 (no extra packages needed).
2. Open a terminal in this folder and run:

   ```
   python server.py
   ```

3. Open http://localhost:8000 in your browser.
4. Stop the server with `Ctrl+C`. The database file `expenses.db` is created automatically on first run.

## Project structure

```
expense-tracker/
├── server.py     # Python backend: serves files + JSON API + SQLite
├── index.html    # Page structure
├── style.css     # Styling
├── script.js     # Frontend logic (fetch calls, rendering, filters)
└── expenses.db   # Created automatically when you first run the server
```

## API

| Method | Endpoint                                   | Purpose                    |
|--------|--------------------------------------------|----------------------------|
| GET    | `/api/expenses?category=Food&month=2026-10`| List expenses and total    |
| POST   | `/api/expenses`                            | Add an expense             |
| PUT    | `/api/expenses/<id>`                       | Update an expense          |
| DELETE | `/api/expenses/<id>`                       | Delete an expense          |
| GET    | `/api/categories`                          | List categories            |

## Resume description (example)

> Built a Personal Expense Tracker web app using HTML, CSS, JavaScript, Python and SQLite, implementing CRUD operations, category and monthly filtering, input validation and a REST-style JSON API without external frameworks.
