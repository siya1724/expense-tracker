"""Personal Expense Tracker - backend.

Uses only the Python standard library (http.server + sqlite3), no Flask.
Serves the frontend files and a small JSON API.

Run:  python server.py
Open: http://localhost:8000
"""

import json
import os
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
PORT = 8000

CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Bills", "Other"]

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/script.js": ("script.js", "application/javascript; charset=utf-8"),
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


# ---------- Database ----------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL CHECK (amount > 0),
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT ''
            )
            """
        )


def validate_expense(data):
    """Return (clean_dict, error_message)."""
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return None, "Amount must be a number."
    if amount <= 0:
        return None, "Amount must be greater than 0."

    category = data.get("category")
    if category not in CATEGORIES:
        return None, "Invalid category."

    date = data.get("date", "")
    if not isinstance(date, str) or not DATE_RE.match(date):
        return None, "Date must be in YYYY-MM-DD format."

    description = str(data.get("description", "")).strip()[:200]

    return {
        "amount": round(amount, 2),
        "category": category,
        "date": date,
        "description": description,
    }, None


# ---------- HTTP handler ----------

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def _expense_id(self, path):
        match = re.fullmatch(r"/api/expenses/(\d+)", path)
        return int(match.group(1)) if match else None

    # --- GET ---
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            try:
                with open(os.path.join(BASE_DIR, filename), "rb") as f:
                    body = f.read()
            except FileNotFoundError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/categories":
            self._send_json(CATEGORIES)
            return

        if path == "/api/expenses":
            params = parse_qs(parsed.query)
            category = params.get("category", [""])[0]
            month = params.get("month", [""])[0]

            query = "SELECT * FROM expenses WHERE 1=1"
            args = []
            if category:
                query += " AND category = ?"
                args.append(category)
            if month:
                if not MONTH_RE.match(month):
                    self._send_error_json(400, "Month must be YYYY-MM.")
                    return
                query += " AND substr(date, 1, 7) = ?"
                args.append(month)
            query += " ORDER BY date DESC, id DESC"

            with get_connection() as conn:
                rows = [dict(r) for r in conn.execute(query, args).fetchall()]
            total = round(sum(r["amount"] for r in rows), 2)
            self._send_json({"expenses": rows, "total": total})
            return

        self.send_error(404)

    # --- POST (create) ---
    def do_POST(self):
        if urlparse(self.path).path != "/api/expenses":
            self.send_error(404)
            return
        data = self._read_json()
        if data is None:
            self._send_error_json(400, "Invalid JSON.")
            return
        clean, error = validate_expense(data)
        if error:
            self._send_error_json(400, error)
            return
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
                (clean["amount"], clean["category"], clean["date"], clean["description"]),
            )
            clean["id"] = cur.lastrowid
        self._send_json(clean, 201)

    # --- PUT (update) ---
    def do_PUT(self):
        expense_id = self._expense_id(urlparse(self.path).path)
        if expense_id is None:
            self.send_error(404)
            return
        data = self._read_json()
        if data is None:
            self._send_error_json(400, "Invalid JSON.")
            return
        clean, error = validate_expense(data)
        if error:
            self._send_error_json(400, error)
            return
        with get_connection() as conn:
            cur = conn.execute(
                "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
                (clean["amount"], clean["category"], clean["date"], clean["description"], expense_id),
            )
            if cur.rowcount == 0:
                self._send_error_json(404, "Expense not found.")
                return
        clean["id"] = expense_id
        self._send_json(clean)

    # --- DELETE ---
    def do_DELETE(self):
        expense_id = self._expense_id(urlparse(self.path).path)
        if expense_id is None:
            self.send_error(404)
            return
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            if cur.rowcount == 0:
                self._send_error_json(404, "Expense not found.")
                return
        self._send_json({"deleted": expense_id})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    init_db()
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Expense Tracker running at http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
