import os
import sqlite3
import secrets
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "abhyuday.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB total form upload


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            qualification TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            experience TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            photo TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            father_name TEXT DEFAULT '',
            mobile TEXT NOT NULL,
            email TEXT DEFAULT '',
            course_id INTEGER,
            address TEXT DEFAULT '',
            dob TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            category TEXT DEFAULT '',
            annual_income TEXT DEFAULT '',
            domicile_state TEXT DEFAULT '',
            domicile_district TEXT DEFAULT '',
            last_qualification TEXT DEFAULT '',
            board_university TEXT DEFAULT '',
            passing_year TEXT DEFAULT '',
            marks_percentage TEXT DEFAULT '',
            character_certificate_no TEXT DEFAULT '',
            photo_file TEXT DEFAULT '',
            signature_file TEXT DEFAULT '',
            income_certificate_file TEXT DEFAULT '',
            domicile_certificate_file TEXT DEFAULT '',
            character_certificate_file TEXT DEFAULT '',
            qualification_file TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            image TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        """)

        # Safe migration: add admission-form fields to existing student databases.
        existing_cols = {row["name"] for row in con.execute("PRAGMA table_info(students)").fetchall()}
        new_cols = {
            "dob": "TEXT DEFAULT ''", "gender": "TEXT DEFAULT ''", "category": "TEXT DEFAULT ''",
            "annual_income": "TEXT DEFAULT ''", "domicile_state": "TEXT DEFAULT ''",
            "domicile_district": "TEXT DEFAULT ''", "last_qualification": "TEXT DEFAULT ''",
            "board_university": "TEXT DEFAULT ''", "passing_year": "TEXT DEFAULT ''",
            "marks_percentage": "TEXT DEFAULT ''", "character_certificate_no": "TEXT DEFAULT ''",
            "photo_file": "TEXT DEFAULT ''", "signature_file": "TEXT DEFAULT ''",
            "income_certificate_file": "TEXT DEFAULT ''", "domicile_certificate_file": "TEXT DEFAULT ''",
            "character_certificate_file": "TEXT DEFAULT ''", "qualification_file": "TEXT DEFAULT ''"
        }
        for col, definition in new_cols.items():
            if col not in existing_cols:
                con.execute(f"ALTER TABLE students ADD COLUMN {col} {definition}")

        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
        exists = con.execute("SELECT id FROM admins WHERE username=?", (username,)).fetchone()
        if not exists:
            con.execute(
                "INSERT INTO admins(username,password_hash) VALUES(?,?)",
                (username, generate_password_hash(password))
            )
        count = con.execute("SELECT COUNT(*) AS n FROM courses").fetchone()["n"]
        if count == 0:
            starter_courses = [
                ("SSC Exams", "SSC CGL, CHSL, MTS एवं अन्य परीक्षाओं की तैयारी।"),
                ("Banking Exams", "Bank PO, Clerk एवं Banking परीक्षाओं की तैयारी।"),
                ("Railway Exams", "RRB NTPC, Group D एवं अन्य Railway परीक्षाएँ।"),
                ("UPSC / State PCS", "Civil Services और State PCS की तैयारी।"),
                ("Police & Defence", "Police, Defence एवं अन्य भर्ती परीक्षाएँ।"),
                ("Other Competitive Exams", "अन्य प्रतियोगी परीक्षाओं के लिए मार्गदर्शन।"),
            ]
            con.executemany("INSERT INTO courses(name,description) VALUES(?,?)", starter_courses)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("केवल JPG, JPEG, PNG या WEBP फोटो अपलोड करें।")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{secrets.token_hex(12)}.{ext}")
    file.save(UPLOAD_DIR / filename)
    return filename


def save_document(file):
    if not file or not file.filename:
        return ""
    allowed = {"pdf", "png", "jpg", "jpeg", "webp"}
    if "." not in file.filename or file.filename.rsplit(".", 1)[1].lower() not in allowed:
        raise ValueError("Documents के लिए केवल PDF, JPG, JPEG, PNG या WEBP file upload करें।")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{secrets.token_hex(12)}.{ext}")
    file.save(UPLOAD_DIR / filename)
    return filename



@app.context_processor
def common_data():
    return {"logged_in": bool(session.get("admin_id"))}


@app.route("/")
def home():
    with db() as con:
        courses = con.execute("SELECT * FROM courses WHERE active=1 ORDER BY name").fetchall()
        faculty = con.execute("SELECT * FROM faculty ORDER BY id DESC LIMIT 6").fetchall()
        gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC LIMIT 8").fetchall()
        student_count = con.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"]
    return render_template("index.html", courses=courses, faculty=faculty,
                           gallery=gallery, student_count=student_count)



@app.route("/register", methods=["GET", "POST"])
def register():
    with db() as con:
        courses = con.execute("SELECT * FROM courses WHERE active=1 ORDER BY name").fetchall()
        if request.method == "POST":
            f = {key: request.form.get(key, "").strip() for key in [
                "name", "father_name", "mobile", "email", "address", "dob", "gender",
                "category", "annual_income", "domicile_state", "domicile_district",
                "last_qualification", "board_university", "passing_year",
                "marks_percentage", "character_certificate_no"
            ]}
            course_id = request.form.get("course_id") or None
            if not f["name"] or not f["mobile"]:
                flash("Student name और mobile number भरना जरूरी है।", "error")
                return render_template("register.html", courses=courses)
            if not f["mobile"].isdigit() or len(f["mobile"]) != 10:
                flash("कृपया 10 अंकों का सही mobile number भरें।", "error")
                return render_template("register.html", courses=courses)

            upload_map = {
                "photo_file": "photo", "signature_file": "signature",
                "income_certificate_file": "income_certificate",
                "domicile_certificate_file": "domicile_certificate",
                "character_certificate_file": "character_certificate",
                "qualification_file": "qualification_document"
            }
            try:
                uploads = {column: save_document(request.files.get(form_name))
                           for column, form_name in upload_map.items()}
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("register.html", courses=courses)

            con.execute("""INSERT INTO students(
                name,father_name,mobile,email,course_id,address,dob,gender,category,
                annual_income,domicile_state,domicile_district,last_qualification,
                board_university,passing_year,marks_percentage,character_certificate_no,
                photo_file,signature_file,income_certificate_file,domicile_certificate_file,
                character_certificate_file,qualification_file
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                f["name"], f["father_name"], f["mobile"], f["email"], course_id, f["address"],
                f["dob"], f["gender"], f["category"], f["annual_income"], f["domicile_state"],
                f["domicile_district"], f["last_qualification"], f["board_university"],
                f["passing_year"], f["marks_percentage"], f["character_certificate_no"],
                uploads["photo_file"], uploads["signature_file"], uploads["income_certificate_file"],
                uploads["domicile_certificate_file"], uploads["character_certificate_file"],
                uploads["qualification_file"]
            ))
            flash("Registration सफल रहा! Registration fee ₹0 है।", "success")
            return redirect(url_for("register"))
    return render_template("register.html", courses=courses)


@app.route("/faculty")
def faculty_page():
    with db() as con:
        faculty = con.execute("SELECT * FROM faculty ORDER BY name").fetchall()
    return render_template("faculty.html", faculty=faculty)


@app.route("/courses")
def courses_page():
    with db() as con:
        courses = con.execute("SELECT * FROM courses WHERE active=1 ORDER BY name").fetchall()
    return render_template("courses.html", courses=courses)


@app.route("/gallery")
def gallery_page():
    with db() as con:
        gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template("gallery.html", gallery=gallery)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as con:
            admin = con.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("dashboard"))
        flash("Username या password गलत है।", "error")
    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    flash("आप logout हो गए हैं।", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def dashboard():
    with db() as con:
        counts = {
            "students": con.execute("SELECT COUNT(*) n FROM students").fetchone()["n"],
            "faculty": con.execute("SELECT COUNT(*) n FROM faculty").fetchone()["n"],
            "courses": con.execute("SELECT COUNT(*) n FROM courses").fetchone()["n"],
            "photos": con.execute("SELECT COUNT(*) n FROM gallery").fetchone()["n"],
        }
        students = con.execute("""SELECT students.*, courses.name course_name
                                  FROM students LEFT JOIN courses ON courses.id=students.course_id
                                  ORDER BY students.id DESC LIMIT 8""").fetchall()
    return render_template("admin/dashboard.html", counts=counts, students=students)


@app.route("/admin/students")
@admin_required
def admin_students():
    with db() as con:
        students = con.execute("""SELECT students.*, courses.name course_name
                                  FROM students LEFT JOIN courses ON courses.id=students.course_id
                                  ORDER BY students.id DESC""").fetchall()
    return render_template("admin/students.html", students=students)



@app.route("/admin/students/<int:student_id>")
@admin_required
def student_detail(student_id):
    with db() as con:
        student = con.execute("""SELECT students.*, courses.name course_name
                                 FROM students LEFT JOIN courses ON courses.id=students.course_id
                                 WHERE students.id=?""", (student_id,)).fetchone()
    if not student:
        abort(404)
    return render_template("admin/student_detail.html", student=student)


@app.route("/admin/students/<int:student_id>/delete", methods=["POST"])
@admin_required
def delete_student(student_id):
    with db() as con:
        con.execute("DELETE FROM students WHERE id=?", (student_id,))
    flash("Student record delete कर दिया गया।", "success")
    return redirect(url_for("admin_students"))


@app.route("/admin/faculty", methods=["GET", "POST"])
@admin_required
def admin_faculty():
    with db() as con:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Faculty name जरूरी है।", "error")
            else:
                try:
                    photo = save_image(request.files.get("photo")) or ""
                    con.execute("""INSERT INTO faculty(name,qualification,subject,experience,bio,photo)
                                   VALUES(?,?,?,?,?,?)""",
                                (name, request.form.get("qualification","").strip(),
                                 request.form.get("subject","").strip(),
                                 request.form.get("experience","").strip(),
                                 request.form.get("bio","").strip(), photo))
                    flash("Faculty profile add हो गई।", "success")
                except ValueError as exc:
                    flash(str(exc), "error")
            return redirect(url_for("admin_faculty"))
        faculty = con.execute("SELECT * FROM faculty ORDER BY id DESC").fetchall()
    return render_template("admin/faculty.html", faculty=faculty)


@app.route("/admin/faculty/<int:faculty_id>/delete", methods=["POST"])
@admin_required
def delete_faculty(faculty_id):
    with db() as con:
        row = con.execute("SELECT photo FROM faculty WHERE id=?", (faculty_id,)).fetchone()
        if row and row["photo"]:
            (UPLOAD_DIR / row["photo"]).unlink(missing_ok=True)
        con.execute("DELETE FROM faculty WHERE id=?", (faculty_id,))
    flash("Faculty profile delete कर दी गई।", "success")
    return redirect(url_for("admin_faculty"))


@app.route("/admin/courses", methods=["GET", "POST"])
@admin_required
def admin_courses():
    with db() as con:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            if name:
                con.execute("INSERT INTO courses(name,description) VALUES(?,?)", (name, description))
                flash("Course add हो गया।", "success")
            return redirect(url_for("admin_courses"))
        courses = con.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    return render_template("admin/courses.html", courses=courses)


@app.route("/admin/courses/<int:course_id>/toggle", methods=["POST"])
@admin_required
def toggle_course(course_id):
    with db() as con:
        con.execute("UPDATE courses SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (course_id,))
    return redirect(url_for("admin_courses"))


@app.route("/admin/gallery", methods=["GET", "POST"])
@admin_required
def admin_gallery():
    with db() as con:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            try:
                image = save_image(request.files.get("image"))
                if not image:
                    flash("कृपया photo चुनें।", "error")
                else:
                    con.execute("INSERT INTO gallery(title,image) VALUES(?,?)", (title, image))
                    flash("Library / coaching photo upload हो गई।", "success")
            except ValueError as exc:
                flash(str(exc), "error")
            return redirect(url_for("admin_gallery"))
        gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template("admin/gallery.html", gallery=gallery)


@app.route("/admin/gallery/<int:photo_id>/delete", methods=["POST"])
@admin_required
def delete_gallery(photo_id):
    with db() as con:
        row = con.execute("SELECT image FROM gallery WHERE id=?", (photo_id,)).fetchone()
        if row:
            (UPLOAD_DIR / row["image"]).unlink(missing_ok=True)
            con.execute("DELETE FROM gallery WHERE id=?", (photo_id,))
    flash("Photo delete कर दी गई।", "success")
    return redirect(url_for("admin_gallery"))


@app.errorhandler(413)
def too_large(_error):
    flash("Photo का size 5 MB से कम रखें।", "error")
    return redirect(request.referrer or url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
