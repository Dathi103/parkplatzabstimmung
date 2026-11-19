import os
import sqlite3
import secrets
import dotenv

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    make_response,
    send_from_directory,
)

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

dotenv.load_dotenv()

TZ = ZoneInfo("Europa/Berlin")
DB = "parking.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise Exception("ADMIN_PASSWORD is not set.")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
)

if not app.secret_key:
    raise Exception("FLASK_SECRET_KEY is not set.")


def parse_day(day: str) -> str | None:
    if not isinstance(day, str):
        return None

    try:
        parsed_day = date.fromisoformat(day)
    except ValueError:
        return None

    if parsed_day.isoformat() != day:
        return None

    return day


def get_connection():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS reservations (

        day TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        token TEXT NOT NULL

    )
    """)

    conn.commit()
    conn.close()


def get_reservations_admin():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM reservations
        ORDER BY day
        """).fetchall()

    conn.close()

    return {row["day"]: dict(row) for row in rows}


def get_reservations_user(token: str | None):

    conn = get_connection()

    rows = conn.execute("""
        SELECT day, name, token
        FROM reservations
        ORDER BY day
        """).fetchall()

    response_dict = {}

    for row in rows:
        response_dict[row["day"]] = {
            "name": row["name"],
            "editable": row["token"] == token,
        }

    conn.close()

    return response_dict


@app.get("/")
def index():
    response = make_response(render_template("index.html"))
    token = request.cookies.get("user_token") or secrets.token_urlsafe(32)
    response.set_cookie(
        "user_token",
        token,
        httponly=True,
        samesite="Lax",
        max_age=60 * 60 * 24 * 365,
    )
    return response


@app.get("/api/reservations")
def reservations():
    user_token = request.cookies.get("user_token")
    return jsonify(get_reservations_user(user_token))


@app.post("/api/reservation")
def reserve():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"success": False, "message": "Ungültige Anfrage"}, 400

    day = parse_day(data.get("day"))
    name = data.get("name", "").strip()
    token = request.cookies.get("user_token")

    if day is None:
        return {"success": False, "message": "Ungültiges Datum"}, 400

    if not name:
        return {"success": False, "message": "Name fehlt"}, 400

    if not token:
        return {"success": False, "message": "User Token fehlt."}, 400

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO reservations
            (day, name, token)
            VALUES (?, ?, ?)
            """,
            (day, name, token),
        )

        conn.commit()

        return {"success": True}

    except sqlite3.IntegrityError:

        return {"success": False, "message": "Tag bereits belegt"}, 400

    finally:

        conn.close()


@app.delete("/api/reservation")
def delete_own_entry():

    data = request.json

    day = data["day"]
    token = request.cookies.get("user_token")

    conn = get_connection()

    row = conn.execute(
        """
        SELECT token
        FROM reservations
        WHERE day = ?
        """,
        (day,),
    ).fetchone()

    if not row:
        return {"success": False, "message": "Eintrag nicht gefunden"}, 404

    if row["token"] != token:
        return {"success": False, "message": "Nicht autorisiert"}, 403

    conn.execute(
        """
        DELETE FROM reservations
        WHERE day = ?
        """,
        (day,),
    )

    conn.commit()

    conn.close()

    return {"success": True}


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        password = request.form.get("password", "")

        if secrets.compare_digest(
            password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8")
        ):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):

        return redirect(url_for("admin"))

    return render_template(
        "admin_dashboard.html", reservations=get_reservations_admin()
    )


@app.route("/admin/delete/<day>", methods=["POST"])
def admin_delete(day):

    if not session.get("admin"):

        return redirect(url_for("admin"))

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM reservations
        WHERE day = ?
        """,
        (day,),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


init_db()

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
