import os
import sqlite3

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

DB = "parking.db"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise Exception("ADMIN_PASSWORD Umgebungsvariable fehlt")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "bitte-spaeter-aendern")


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


def get_reservations():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM reservations
        ORDER BY day
        """).fetchall()

    conn.close()

    return {row["day"]: dict(row) for row in rows}


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/api/reservations")
def reservations():

    return jsonify(get_reservations())


@app.route("/api/reserve", methods=["POST"])
def reserve():

    data = request.json

    day = data["day"]
    name = data["name"].strip()
    token = data["token"]

    if not name:

        return {"success": False, "message": "Name fehlt"}, 400

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


@app.route("/api/delete", methods=["POST"])
def delete_own_entry():

    data = request.json

    day = data["day"]
    token = data["token"]

    conn = get_connection()

    row = conn.execute(
        """
        SELECT token
        FROM reservations
        WHERE day = ?
        """,
        (day,),
    ).fetchone()

    if row and row["token"] == token:

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

        if password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):

        return redirect(url_for("admin"))

    return render_template("admin_dashboard.html", reservations=get_reservations())


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


init_db()

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
