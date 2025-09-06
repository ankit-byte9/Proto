from flask import Flask, request, jsonify
import sqlite3
import os
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Automatically select persistent or temp data dir
PERSISTENT_DIR = "/mnt/data"
TMP_DIR = "/tmp/data"

# Root Route [changed by : Ayush]
# -->
@app.route("/", methods=["GET"])
def home():
    return jsonify({"success": True, "message": "Server is Running"})
# ---

def get_data_dir():
    # If persistent disk exists and is writable, use it
    if os.path.exists(PERSISTENT_DIR) and os.access(PERSISTENT_DIR, os.W_OK):
        return PERSISTENT_DIR
    # Otherwise, fall back to /tmp/data
    return TMP_DIR

DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "attendance.db")
IMAGE_FOLDER = os.path.join(DATA_DIR, "student_images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Database Setup 
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# Teacher Verification 
def verify_teacher(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM teachers WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Routes 

# Student Registration
@app.route("/student/register", methods=["POST"])
def register_student():
    try:
        name = request.form.get("name")
        image = request.files.get("image")

        if not name or not image:
            return jsonify({"success": False, "error": "Name and image required"}), 400

        # Save image to persistent folder
        image_path = os.path.join(IMAGE_FOLDER, f"{name}_{image.filename}")
        image.save(image_path)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO students (name, image_path) VALUES (?, ?)", (name, image_path))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Student {name} registered successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# Teacher Login
@app.route("/teacher/login", methods=["POST"])
def teacher_login():
    try:
        username = request.form.get("username")
        password = request.form.get("password")

        teacher_id = verify_teacher(username, password)
        if not teacher_id:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        return jsonify({"success": True, "message": "Login successful", "teacher_id": teacher_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# Mark Attendance
@app.route("/teacher/attendance", methods=["POST"])
def mark_attendance():
    try:
        data = request.json
        recognized_students = data.get("recognized_students", [])

        present_students = []
        unidentifiable_students = []

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        for student in recognized_students:
            sid = student.get("id")
            confidence = student.get("confidence", 1.0)

            if confidence >= 0.5:
                c.execute("UPDATE students SET present=1 WHERE id=?", (sid,))
                present_students.append(sid)
            else:
                unidentifiable_students.append(sid)

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "present_students": present_students,
            "unidentifiable_students": unidentifiable_students
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# Manual Mark
@app.route("/teacher/manual_mark", methods=["POST"])
def manual_mark():
    try:
        student_id = request.form.get("student_id")
        status = request.form.get("status")  # "present" or "absent"

        if not student_id or status not in ["present", "absent"]:
            return jsonify({"success": False, "error": "Invalid input"}), 400

        present_value = 1 if status == "present" else 0

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE students SET present=? WHERE id=?", (present_value, student_id))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Student {student_id} marked as {status}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# List Students
@app.route("/students", methods=["GET"])
def list_students():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, present FROM students")
        rows = c.fetchall()
        conn.close()

        students = [
            {"id": row[0], "name": row[1], "status": "present" if row[2] == 1 else "absent"}
            for row in rows
        ]
        return jsonify({"students": students})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# Seed Teacher
def seed_teacher():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO teachers (username, password) VALUES (?, ?)", ("teacher1", "1234"))
    conn.commit()
    conn.close()

# Global error handler: returns JSON instead of HTML for 500 errors
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500

# Initialization (runs at import, not just __main__)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
init_db()
seed_teacher()

# Main 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
