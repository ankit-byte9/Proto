from flask import Flask, request, jsonify
import sqlite3
import os
import requests

app = Flask(__name__)

# Folder for saving student images
IMAGE_FOLDER = "student_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------------- Database Setup ---------------- #
def init_db():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT,
            present INTEGER DEFAULT 0
        )
    """)

    # Teachers table
    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- Teacher Verification ---------------- #
def verify_teacher(username, password):
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("SELECT id FROM teachers WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


# ---------------- Routes ---------------- #

# Student Registration (with image storage)
@app.route("/student/register", methods=["POST"])
def register_student():
    name = request.form.get("name")
    image = request.files.get("image")

    if not name or not image:
        return jsonify({"success": False, "error": "Name and image required"}), 400

    # Save image to disk
    image_path = os.path.join(IMAGE_FOLDER, f"{name}_{image.filename}")
    image.save(image_path)

    # Insert into DB
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("INSERT INTO students (name, image_path) VALUES (?, ?)", (name, image_path))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Student {name} registered successfully"})


# Teacher login + Attendance marking
@app.route("/teacher/login", methods=["POST"])
def teacher_login():
    username = request.form.get("username")
    password = request.form.get("password")
    image = request.files.get("image")  # Class photo

    teacher_id = verify_teacher(username, password)
    if not teacher_id:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    if not image:
        return jsonify({"success": False, "error": "No image uploaded"}), 400

    # Send image to ML API
    ml_api_url = "http://ml-api-url/recognize"  # Replace with your ML endpoint
    files = {"image": (image.filename, image.stream, image.mimetype)}
    response = requests.post(ml_api_url, files=files)

    if response.status_code != 200:
        return jsonify({"success": False, "error": "ML API error"}), 500

    # Assume ML API returns: {"recognized": [{"id": 1, "confidence": 0.9}, {"id": 2, "confidence": 0.4}]}
    results = response.json().get("recognized", [])

    present_students = []
    unidentifiable_students = []

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    for r in results:
        sid = r["id"]
        confidence = r["confidence"]

        if confidence >= 0.5:  # >= 50% → mark present
            c.execute("UPDATE students SET present=1 WHERE id=?", (sid,))
            present_students.append(sid)
        else:  # < 50% → needs manual marking
            unidentifiable_students.append(sid)

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "present_students": present_students,
        "unidentifiable_students": unidentifiable_students
    })


# Teacher can manually mark attendance for unidentifiable students
@app.route("/teacher/manual_mark", methods=["POST"])
def manual_mark():
    student_id = request.form.get("student_id")
    status = request.form.get("status")  # "present" or "absent"

    if not student_id or status not in ["present", "absent"]:
        return jsonify({"success": False, "error": "Invalid input"}), 400

    present_value = 1 if status == "present" else 0

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("UPDATE students SET present=? WHERE id=?", (present_value, student_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Student {student_id} marked as {status}"})


# List all students with their status
@app.route("/students", methods=["GET"])
def list_students():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("SELECT id, name, present FROM students")
    rows = c.fetchall()
    conn.close()

    students = [
        {"id": row[0], "name": row[1], "status": "present" if row[2] == 1 else "absent"}
        for row in rows
    ]
    return jsonify({"students": students})


# ---------------- Seed Teacher ---------------- #
def seed_teacher():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO teachers (username, password) VALUES (?, ?)", ("teacher1", "1234"))
    conn.commit()
    conn.close()


# ---------------- Main ---------------- #
if __name__ == "__main__":
    init_db()
    seed_teacher()
    app.run(debug=True)
