from flask import (Flask, send_from_directory, render_template,
                   abort, request, Response, jsonify, session, redirect, url_for)
from pathlib import Path
import os, io, sqlite3, datetime, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)   # neu bei jedem Start — für Produktion fixen Wert setzen

ROOT       = Path("Q:/")
DB_PATH    = Path("visitors.db")
ADMIN_PASS = "admin123"          # <-- hier Passwort ändern!
ADMIN_PATH = "geheim-admin"      # <-- geheime URL: /geheim-admin

AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
VIDEO_EXT = {".mp4", ".webm", ".mkv", ".mov", ".avi"}

# ── DB Setup ──────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id          TEXT PRIMARY KEY,
                ip          TEXT,
                user_agent  TEXT,
                first_seen  TEXT,
                last_seen   TEXT,
                visits      INTEGER DEFAULT 1,
                pages       TEXT DEFAULT ''
            )
        """)

init_db()

# ── Helpers ───────────────────────────────────────────────────
def file_type(name):
    ext = Path(name).suffix.lower()
    if ext in AUDIO_EXT: return "audio"
    if ext in IMAGE_EXT: return "image"
    if ext in VIDEO_EXT: return "video"
    return "file"

def safe_path(rel):
    path = (ROOT / rel).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        abort(403)
    return path

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Visitor Tracking API ──────────────────────────────────────
@app.route("/api/visit", methods=["POST"])
def api_visit():
    data      = request.get_json(silent=True) or {}
    visitor_id = data.get("id", "")[:64]
    page       = data.get("page", "/")[:200]
    ip         = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua         = request.user_agent.string[:300]

    if not visitor_id or len(visitor_id) < 8:
        return jsonify({"ok": False}), 400

    with get_db() as db:
        row = db.execute("SELECT * FROM visitors WHERE id=?", (visitor_id,)).fetchone()
        if row:
            pages = set(row["pages"].split("|")) if row["pages"] else set()
            pages.add(page)
            db.execute("""
                UPDATE visitors SET ip=?, user_agent=?, last_seen=?, visits=visits+1, pages=?
                WHERE id=?
            """, (ip, ua, now(), "|".join(pages), visitor_id))
        else:
            db.execute("""
                INSERT INTO visitors (id, ip, user_agent, first_seen, last_seen, pages)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (visitor_id, ip, ua, now(), now(), page))

    return jsonify({"ok": True})

# ── Admin Panel ───────────────────────────────────────────────
@app.route(f"/{ADMIN_PATH}", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
        else:
            return render_template("admin.html", error="Falsches Passwort", logged_in=False)

    if not session.get("admin"):
        return render_template("admin.html", logged_in=False)

    with get_db() as db:
        visitors = db.execute(
            "SELECT * FROM visitors ORDER BY last_seen DESC"
        ).fetchall()

    return render_template("admin.html", logged_in=True, visitors=visitors)

@app.route(f"/{ADMIN_PATH}/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(f"/{ADMIN_PATH}")

@app.route(f"/{ADMIN_PATH}/delete/<visitor_id>", methods=["POST"])
def admin_delete(visitor_id):
    if not session.get("admin"):
        abort(403)
    with get_db() as db:
        db.execute("DELETE FROM visitors WHERE id=?", (visitor_id,))
    return redirect(f"/{ADMIN_PATH}")

# ── File Browser ──────────────────────────────────────────────
@app.route("/", defaults={"rel": ""})
@app.route("/browse/<path:rel>")
def browse(rel):
    path = safe_path(rel)
    if not path.exists() or not path.is_dir():
        abort(404)

    entries = []
    for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        entries.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "type": "folder" if item.is_dir() else file_type(item.name),
            "rel": str(Path(rel) / item.name).replace("\\", "/"),
            "size": f"{item.stat().st_size / 1024 / 1024:.1f} MB" if item.is_file() else "",
        })

    parts = [p for p in rel.split("/") if p]
    breadcrumbs = [("Q:/", "")]
    for i, p in enumerate(parts):
        breadcrumbs.append((p, "/".join(parts[:i+1])))

    return render_template("index.html", entries=entries, breadcrumbs=breadcrumbs, rel=rel)

@app.route("/file/<path:rel>")
def serve_file(rel):
    path = safe_path(rel)
    if not path.is_file():
        abort(404)
    return send_from_directory(path.parent, path.name)

@app.route("/download/<path:rel>")
def download(rel):
    path = safe_path(rel)
    if not path.is_file():
        abort(404)
    return send_from_directory(path.parent, path.name, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
