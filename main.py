from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                                RedirectResponse, StreamingResponse)
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import aiosqlite, datetime, re, json, logging, mimetypes, time
from logging.handlers import RotatingFileHandler
from collections import defaultdict

app = FastAPI()

CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))

app.add_middleware(SessionMiddleware, secret_key=CONFIG["secret_key"])

templates = Jinja2Templates(directory="templates")

# ── Logging ────────────────────────────────────────────────────
def setup_logging():
    level = getattr(logging, CONFIG.get("log_level", "INFO").upper(), logging.INFO)
    handler = RotatingFileHandler(
        CONFIG.get("log_file", "server.log"),
        maxBytes=CONFIG.get("log_max_bytes", 5_242_880),
        backupCount=CONFIG.get("log_backup_count", 3),
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)

setup_logging()
log = logging.getLogger(__name__)

ROOT       = Path(CONFIG["root_path"])
DB_PATH    = "visitors.db"
ADMIN_PASS = CONFIG["admin_password"]
ADMIN_PATH = CONFIG["admin_path"]

AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
VIDEO_EXT = {".mp4", ".webm", ".mkv", ".mov", ".avi"}

# rate limit: max 5 failed attempts per 5 minutes per IP
_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_SECS  = 300

# ── DB ─────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id         TEXT PRIMARY KEY,
                ip         TEXT,
                user_agent TEXT,
                first_seen TEXT,
                last_seen  TEXT,
                visits     INTEGER DEFAULT 1,
                pages      TEXT DEFAULT ''
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_last_seen ON visitors(last_seen)"
        )
        await db.commit()

@app.on_event("startup")
async def startup():
    await init_db()
    log.info("Server started — root=%s", ROOT)

# ── Request logging middleware ─────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    ip  = request.headers.get("X-Forwarded-For", request.client.host)
    msg = f"{ip} {request.method} {request.url.path} {response.status_code}"
    if response.status_code >= 500:
        log.error(msg)
    elif response.status_code >= 400:
        log.warning(msg)
    else:
        log.info(msg)
    return response

# ── Helpers ────────────────────────────────────────────────────
def file_type(name: str) -> str:
    ext = Path(name).suffix.lower()
    if ext in AUDIO_EXT: return "audio"
    if ext in IMAGE_EXT: return "image"
    if ext in VIDEO_EXT: return "video"
    return "file"

def safe_path(rel: str) -> Path:
    path = (ROOT / rel).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        raise HTTPException(403)
    return path

def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_rate_limited(ip: str) -> bool:
    cutoff   = time.time() - WINDOW_SECS
    attempts = [t for t in _login_attempts[ip] if t > cutoff]
    _login_attempts[ip] = attempts
    return len(attempts) >= MAX_ATTEMPTS

def record_failed_attempt(ip: str):
    _login_attempts[ip].append(time.time())

# ── Visitor Tracking ───────────────────────────────────────────
@app.post("/api/visit")
async def api_visit(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)

    visitor_id = str(data.get("id", ""))[:64]
    page       = str(data.get("page", "/"))[:200]
    ip         = request.headers.get("X-Forwarded-For", request.client.host)
    ua         = request.headers.get("user-agent", "")[:300]

    if not visitor_id or len(visitor_id) < 8:
        return JSONResponse({"ok": False}, status_code=400)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(
            "SELECT * FROM visitors WHERE id=?", (visitor_id,)
        )).fetchone()
        if row:
            pages = set(row["pages"].split("|")) if row["pages"] else set()
            pages.add(page)
            await db.execute("""
                UPDATE visitors
                SET ip=?, user_agent=?, last_seen=?, visits=visits+1, pages=?
                WHERE id=?
            """, (ip, ua, now(), "|".join(pages), visitor_id))
        else:
            await db.execute("""
                INSERT INTO visitors (id, ip, user_agent, first_seen, last_seen, pages)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (visitor_id, ip, ua, now(), now(), page))
        await db.commit()

    return JSONResponse({"ok": True})

# ── Admin ──────────────────────────────────────────────────────
@app.get(f"/{ADMIN_PATH}", response_class=HTMLResponse)
async def admin_get(request: Request):
    if not request.session.get("admin"):
        return templates.TemplateResponse(
            "admin.html", {"request": request, "logged_in": False, "config": CONFIG}
        )
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM visitors ORDER BY last_seen DESC"
        )).fetchall()
        visitors = [dict(r) for r in rows]
    return templates.TemplateResponse("admin.html", {
        "request": request, "logged_in": True, "visitors": visitors, "config": CONFIG
    })

@app.post(f"/{ADMIN_PATH}", response_class=HTMLResponse)
async def admin_post(request: Request, password: str = Form(...)):
    ip = request.headers.get("X-Forwarded-For", request.client.host)

    if is_rate_limited(ip):
        log.warning("Admin login rate limited — ip=%s", ip)
        return templates.TemplateResponse("admin.html", {
            "request": request, "logged_in": False,
            "error": "Too many attempts. Wait 5 minutes.", "config": CONFIG
        })

    if password == ADMIN_PASS:
        request.session["admin"] = True
        log.info("Admin login success — ip=%s", ip)
        return RedirectResponse(f"/{ADMIN_PATH}", status_code=303)

    record_failed_attempt(ip)
    log.warning("Admin login failed — ip=%s", ip)
    return templates.TemplateResponse("admin.html", {
        "request": request, "logged_in": False, "error": "Wrong password", "config": CONFIG
    })

@app.get(f"/{ADMIN_PATH}/logout")
async def admin_logout(request: Request):
    request.session.pop("admin", None)
    return RedirectResponse(f"/{ADMIN_PATH}", status_code=303)

@app.post(f"/{ADMIN_PATH}/delete/{{visitor_id}}")
async def admin_delete(visitor_id: str, request: Request):
    if not request.session.get("admin"):
        raise HTTPException(403)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM visitors WHERE id=?", (visitor_id,))
        await db.commit()
    return RedirectResponse(f"/{ADMIN_PATH}", status_code=303)

# ── File Browser ───────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/browse/{rel:path}", response_class=HTMLResponse)
async def browse(request: Request, rel: str = ""):
    path = safe_path(rel)
    if not path.exists() or not path.is_dir():
        raise HTTPException(404)

    entries = []
    for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        entries.append({
            "name":   item.name,
            "is_dir": item.is_dir(),
            "type":   "folder" if item.is_dir() else file_type(item.name),
            "rel":    str(Path(rel) / item.name).replace("\\", "/"),
            "size":   f"{item.stat().st_size / 1024 / 1024:.1f} MB" if item.is_file() else "",
        })

    parts       = [p for p in rel.split("/") if p]
    breadcrumbs = [("Root", "")]
    for i, p in enumerate(parts):
        breadcrumbs.append((p, "/".join(parts[: i + 1])))

    return templates.TemplateResponse("index.html", {
        "request": request, "entries": entries,
        "breadcrumbs": breadcrumbs, "rel": rel, "config": CONFIG,
    })

# ── File serving with Range support (audio scrubbing) ─────────
@app.get("/file/{rel:path}")
async def serve_file(rel: str, request: Request):
    path = safe_path(rel)
    if not path.is_file():
        raise HTTPException(404)

    file_size    = path.stat().st_size
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    range_header = request.headers.get("range")

    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end   = int(match.group(2)) if match.group(2) else file_size - 1
            end   = min(end, file_size - 1)
            length = end - start + 1

            def iter_file():
                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(65536, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                iter_file(),
                status_code=206,
                headers={
                    "Content-Range":  f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges":  "bytes",
                    "Content-Length": str(length),
                    "Content-Type":   content_type,
                },
            )

    return FileResponse(path, headers={"Accept-Ranges": "bytes"})

@app.get("/download/{rel:path}")
async def download(rel: str, request: Request):
    path = safe_path(rel)
    if not path.is_file():
        raise HTTPException(404)
    ip = request.headers.get("X-Forwarded-For", request.client.host)
    log.info("Download — ip=%s file=%s", ip, rel)
    return FileResponse(path, filename=path.name)
