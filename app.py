import os
import sqlite3
import secrets
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DB_PATH = BASE_DIR / "footrate.db"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FOOTRATE_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # max 5 MB
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
# The admin account is selected by the hosting environment, never by a public form.
app.config["ADMIN_USERNAME"] = os.environ.get("FOOTRATE_ADMIN_USERNAME", "Axel").strip()
CSRFProtect(app)

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
                UNIQUE(photo_id, user_id)
            );
        """)


init_db()


def is_admin():
    configured_admin = app.config.get("ADMIN_USERNAME", "")
    current_username = session.get("username", "")
    return bool(configured_admin and current_username and current_username.casefold() == configured_admin.casefold())


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    return response


@app.route("/")
@login_required
def index():
    with connect_db() as db:
        photos = db.execute("""
            SELECT p.id, p.filename, p.user_id, u.username,
                   ROUND(AVG(r.score), 1) AS average,
                   COUNT(r.id) AS rating_count,
                   mine.score AS my_score
            FROM photos p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN ratings r ON r.photo_id = p.id
            LEFT JOIN ratings mine ON mine.photo_id = p.id AND mine.user_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """, (session["user_id"],)).fetchall()
    return render_template("index.html", photos=photos, username=session["username"], admin=is_admin())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not 3 <= len(username) <= 20 or not all(c.isalnum() or c in "_-" for c in username):
            flash("A felhasználónév 3–20 karakter legyen; betű, szám, _ és - használható.")
            return render_template("register.html")
        if len(password) < 8:
            flash("A jelszó legalább 8 karakter legyen.")
            return render_template("register.html")
        try:
            with connect_db() as db:
                cur = db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                user_id = cur.lastrowid
        except sqlite3.IntegrityError:
            flash("Ez a felhasználónév már foglalt.")
            return render_template("register.html")
        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with connect_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Hibás felhasználónév vagy jelszó.")
            return render_template("login.html")
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("photo")
    if not file or not file.filename:
        flash("Válassz ki egy képet.")
        return redirect(url_for("index"))
    original = secure_filename(file.filename)
    if Path(original).suffix.lower() not in ALLOWED_EXTENSIONS:
        flash("Csak JPG, PNG vagy WEBP kép tölthető fel.")
        return redirect(url_for("index"))
    # Decode and verify the actual image rather than trusting the filename/MIME type.
    try:
        file.stream.seek(0)
        image = Image.open(file.stream)
        if image.format not in ALLOWED_FORMATS:
            raise ValueError("Unsupported image format")
        image.verify()
        file.stream.seek(0)
        image = Image.open(file.stream)
        image.thumbnail((1600, 1600))
        filename = f"{secrets.token_hex(16)}.jpg"
        destination = UPLOAD_DIR / filename
        image.convert("RGB").save(destination, "JPEG", quality=88, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError):
        flash("A fájl nem érvényes kép.")
        return redirect(url_for("index"))
    with connect_db() as db:
        db.execute("INSERT INTO photos (user_id, filename) VALUES (?, ?)",
                   (session["user_id"], filename))
    flash("A képed feltöltve.")
    return redirect(url_for("index"))


@app.route("/rate/<int:photo_id>", methods=["POST"])
@login_required
def rate(photo_id):
    score_text = request.form.get("score", "")
    try:
        score = int(score_text)
    except ValueError:
        abort(400)
    if not 1 <= score <= 10:
        abort(400)
    with connect_db() as db:
        photo = db.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if not photo:
            abort(404)
        if photo["user_id"] == session["user_id"]:
            flash("A saját képedet nem értékelheted.")
            return redirect(url_for("index"))
        existing = db.execute(
            "SELECT id FROM ratings WHERE photo_id = ? AND user_id = ?",
            (photo_id, session["user_id"])
        ).fetchone()
        if existing:
            db.execute("UPDATE ratings SET score = ? WHERE id = ?", (score, existing["id"]))
            flash("Az értékelésed frissítve.")
        else:
            db.execute("INSERT INTO ratings (photo_id, user_id, score) VALUES (?, ?, ?)",
                       (photo_id, session["user_id"], score))
            flash("Értékelés mentve.")
    return redirect(url_for("index"))


@app.route("/delete/<int:photo_id>", methods=["POST"])
@login_required
def delete_photo(photo_id):
    with connect_db() as db:
        photo = db.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if not photo:
            abort(404)
        if photo["user_id"] != session["user_id"] and not is_admin():
            abort(403)
        db.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    try:
        (UPLOAD_DIR / photo["filename"]).unlink(missing_ok=True)
    except OSError:
        pass
    flash("Kép törölve.")
    return redirect(url_for("index"))


@app.errorhandler(413)
def too_large(_error):
    flash("A kép túl nagy. A maximális méret 5 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
