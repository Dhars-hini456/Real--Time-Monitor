"""
Online Issuance of Caste and Other Certificates by Revenue Department
Main Flask Application (uses Python's built-in sqlite3 module)
"""
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                    session, flash, send_from_directory, abort, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import database as db
from certificate_generator import generate_certificate_pdf

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
CERT_FOLDER = os.path.join(BASE_DIR, "static", "certificates")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "revenue-dept-certificate-portal-secret-key-2024"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

CERT_TYPES = ["Caste Certificate", "Income Certificate", "Community Certificate",
              "Nativity Certificate", "Residence Certificate"]

DOC_TYPES = ["Photo", "Aadhaar / ID Proof", "Address Proof", "Ration Card",
             "Income Proof", "Other Supporting Document"]

STATUS_PENDING = "Pending"
STATUS_FORWARDED = "Forwarded"
STATUS_APPROVED = "Approved"
STATUS_REJECTED = "Rejected"


# ---------------------------------------------------------------------------
# Database connection lifecycle (per request)
# ---------------------------------------------------------------------------
def get_db():
    if "db_conn" not in g:
        g.db_conn = db.get_connection()
    return g.db_conn


@app.teardown_appcontext
def close_db(exception=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_application_no():
    return "RD" + datetime.now().strftime("%Y%m%d") + str(uuid.uuid4().int)[:6]


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login to continue.", "warning")
                if role == "officer":
                    return redirect(url_for("officer_login"))
                elif role == "admin":
                    return redirect(url_for("admin_login"))
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You are not authorized to view that page.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def find_user_by_email(email, role=None):
    conn = get_db()
    if role:
        row = conn.execute("SELECT * FROM users WHERE email = ? AND role = ?",
                            (email, role)).fetchone()
    else:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return row


def find_user_by_id(user_id):
    conn = get_db()
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return find_user_by_id(uid)


def get_application(app_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    return row


def get_documents(app_id):
    conn = get_db()
    return conn.execute("SELECT * FROM documents WHERE application_id = ? ORDER BY id",
                         (app_id,)).fetchall()


def parse_dt(value):
    """Parse a sqlite datetime string into a python datetime object for templates."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


@app.context_processor
def inject_globals():
    return dict(current_user=current_user(), cert_types=CERT_TYPES,
                 now=datetime.utcnow())


app.jinja_env.filters["parse_dt"] = parse_dt


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not (full_name and email and password):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))
        if find_user_by_email(email):
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        conn.execute(
            "INSERT INTO users (full_name, email, phone, address, password_hash, role) "
            "VALUES (?, ?, ?, ?, ?, 'citizen')",
            (full_name, email, phone, address, generate_password_hash(password))
        )
        conn.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email, role="citizen")
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = "citizen"
            session["name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("citizen_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Citizen routes
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required(role="citizen")
def citizen_dashboard():
    conn = get_db()
    apps = conn.execute(
        "SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()
    stats = {
        "total": len(apps),
        "pending": len([a for a in apps if a["status"] in (STATUS_PENDING, STATUS_FORWARDED)]),
        "approved": len([a for a in apps if a["status"] == STATUS_APPROVED]),
        "rejected": len([a for a in apps if a["status"] == STATUS_REJECTED]),
    }
    return render_template("citizen_dashboard.html", applications=apps, stats=stats)


@app.route("/apply", methods=["GET", "POST"])
@login_required(role="citizen")
def apply_certificate():
    if request.method == "POST":
        cert_type = request.form.get("cert_type")
        if cert_type not in CERT_TYPES:
            flash("Please select a valid certificate type.", "danger")
            return redirect(url_for("apply_certificate"))

        conn = get_db()
        application_no = generate_application_no()
        cur = conn.execute(
            """INSERT INTO applications
               (application_no, user_id, cert_type, applicant_name, father_name, dob,
                gender, caste, religion, annual_income, address, district, taluk,
                village, purpose, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (application_no, session["user_id"], cert_type,
             request.form.get("applicant_name", "").strip(),
             request.form.get("father_name", "").strip(),
             request.form.get("dob", "").strip(),
             request.form.get("gender", "").strip(),
             request.form.get("caste", "").strip(),
             request.form.get("religion", "").strip(),
             request.form.get("annual_income", "").strip(),
             request.form.get("address", "").strip(),
             request.form.get("district", "").strip(),
             request.form.get("taluk", "").strip(),
             request.form.get("village", "").strip(),
             request.form.get("purpose", "").strip(),
             STATUS_PENDING)
        )
        application_id = cur.lastrowid

        files = request.files.getlist("documents")
        doc_types = request.form.getlist("doc_type")
        app_folder = os.path.join(UPLOAD_FOLDER, str(application_id))
        os.makedirs(app_folder, exist_ok=True)

        for idx, f in enumerate(files):
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit(".", 1)[1].lower()
                stored_name = f"{uuid.uuid4().hex}.{ext}"
                f.save(os.path.join(app_folder, stored_name))
                doc_type = doc_types[idx] if idx < len(doc_types) else "Other"
                conn.execute(
                    "INSERT INTO documents (application_id, doc_type, original_name, stored_name) "
                    "VALUES (?, ?, ?, ?)",
                    (application_id, doc_type, secure_filename(f.filename), stored_name)
                )

        conn.commit()
        flash(f"Application submitted successfully! Your application number is {application_no}", "success")
        return redirect(url_for("citizen_dashboard"))

    return render_template("apply_certificate.html", cert_types=CERT_TYPES, doc_types=DOC_TYPES)


@app.route("/application/<int:app_id>")
@login_required(role="citizen")
def view_application(app_id):
    application = get_application(app_id)
    if not application:
        abort(404)
    if application["user_id"] != session["user_id"]:
        abort(403)
    documents = get_documents(app_id)
    return render_template("application_detail.html", application=application, documents=documents)


@app.route("/uploads/<int:app_id>/<filename>")
@login_required()
def uploaded_file(app_id, filename):
    application = get_application(app_id)
    if not application:
        abort(404)
    if session.get("role") == "citizen" and application["user_id"] != session["user_id"]:
        abort(403)
    return send_from_directory(os.path.join(UPLOAD_FOLDER, str(app_id)), filename)


@app.route("/download_certificate/<int:app_id>")
@login_required()
def download_certificate(app_id):
    application = get_application(app_id)
    if not application:
        abort(404)
    if session.get("role") == "citizen" and application["user_id"] != session["user_id"]:
        abort(403)
    if application["status"] != STATUS_APPROVED or not application["certificate_path"]:
        flash("Certificate is not available yet.", "warning")
        return redirect(url_for("index"))
    return send_from_directory(CERT_FOLDER, application["certificate_path"], as_attachment=True)


# ---------------------------------------------------------------------------
# Revenue Officer routes
# ---------------------------------------------------------------------------
@app.route("/officer/login", methods=["GET", "POST"])
def officer_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email, role="officer")
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = "officer"
            session["name"] = user["full_name"]
            flash(f"Welcome, {user['full_name']}!", "success")
            return redirect(url_for("officer_dashboard"))
        flash("Invalid officer credentials.", "danger")
    return render_template("officer_login.html")


@app.route("/officer/dashboard")
@login_required(role="officer")
def officer_dashboard():
    conn = get_db()
    status_filter = request.args.get("status", "all")
    if status_filter != "all":
        apps = conn.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
            (status_filter,)
        ).fetchall()
    else:
        apps = conn.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()

    counts = {
        "all": conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
        "Pending": conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                                 (STATUS_PENDING,)).fetchone()[0],
        "Approved": conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                                  (STATUS_APPROVED,)).fetchone()[0],
        "Rejected": conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                                  (STATUS_REJECTED,)).fetchone()[0],
    }
    return render_template("officer_dashboard.html", applications=apps,
                            counts=counts, status_filter=status_filter, admin_view=False)


@app.route("/officer/application/<int:app_id>", methods=["GET", "POST"])
@login_required(role="officer")
def officer_view_application(app_id):
    conn = get_db()
    application = get_application(app_id)
    if not application:
        abort(404)

    if request.method == "POST":
        action = request.form.get("action")
        remarks = request.form.get("remarks", "").strip()

        if action == "approve":
            officer = find_user_by_id(session["user_id"])
            applicant = find_user_by_id(application["user_id"])
            cert_filename = generate_certificate_pdf(application, officer, CERT_FOLDER)
            conn.execute(
                "UPDATE applications SET status = ?, remarks = ?, officer_id = ?, "
                "certificate_path = ?, updated_at = datetime('now') WHERE id = ?",
                (STATUS_APPROVED, remarks, session["user_id"], cert_filename, app_id)
            )
            flash("Application approved and certificate generated.", "success")
        elif action == "reject":
            conn.execute(
                "UPDATE applications SET status = ?, remarks = ?, officer_id = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (STATUS_REJECTED, remarks, session["user_id"], app_id)
            )
            flash("Application rejected.", "info")

        conn.commit()
        return redirect(url_for("officer_dashboard"))

    documents = get_documents(app_id)
    applicant = find_user_by_id(application["user_id"])
    officer = find_user_by_id(application["officer_id"]) if application["officer_id"] else None
    return render_template("view_application.html", application=application, documents=documents,
                            applicant=applicant, officer=officer, role="officer")


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email, role="admin")
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = "admin"
            session["name"] = user["full_name"]
            flash(f"Welcome, {user['full_name']}!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    conn = get_db()
    total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                            (STATUS_PENDING,)).fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                             (STATUS_APPROVED,)).fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM applications WHERE status = ?",
                             (STATUS_REJECTED,)).fetchone()[0]
    citizens = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'citizen'").fetchone()[0]
    officers = conn.execute("SELECT * FROM users WHERE role = 'officer'").fetchall()
    recent_apps = conn.execute("SELECT * FROM applications ORDER BY created_at DESC LIMIT 10").fetchall()
    return render_template("admin_dashboard.html", total_apps=total_apps, pending=pending,
                            approved=approved, rejected=rejected, citizens=citizens,
                            officers=officers, recent_apps=recent_apps)


@app.route("/admin/applications")
@login_required(role="admin")
def admin_applications():
    conn = get_db()
    apps = conn.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()
    return render_template("officer_dashboard.html", applications=apps,
                            counts=None, status_filter="all", admin_view=True)


@app.route("/admin/application/<int:app_id>")
@login_required(role="admin")
def admin_view_application(app_id):
    application = get_application(app_id)
    if not application:
        abort(404)
    documents = get_documents(app_id)
    applicant = find_user_by_id(application["user_id"])
    officer = find_user_by_id(application["officer_id"]) if application["officer_id"] else None
    return render_template("view_application.html", application=application, documents=documents,
                            applicant=applicant, officer=officer, role="admin")


@app.route("/admin/officers/add", methods=["GET", "POST"])
@login_required(role="admin")
def add_officer():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if find_user_by_email(email):
            flash("A user with this email already exists.", "danger")
            return redirect(url_for("add_officer"))

        conn = get_db()
        conn.execute(
            "INSERT INTO users (full_name, email, phone, password_hash, role) "
            "VALUES (?, ?, ?, ?, 'officer')",
            (full_name, email, phone, generate_password_hash(password))
        )
        conn.commit()
        flash("Revenue Officer account created successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_officer.html")


@app.route("/admin/officers/delete/<int:officer_id>")
@login_required(role="admin")
def delete_officer(officer_id):
    conn = get_db()
    officer = find_user_by_id(officer_id)
    if officer and officer["role"] == "officer":
        conn.execute("DELETE FROM users WHERE id = ?", (officer_id,))
        conn.commit()
        flash("Officer account removed.", "info")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("404.html", message="Access Forbidden (403)"), 403


# ---------------------------------------------------------------------------
# Database initialization (seed default admin & officer accounts)
# ---------------------------------------------------------------------------
def init_app_db():
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(CERT_FOLDER, exist_ok=True)
    db.init_db()

    conn = db.get_connection()
    if not conn.execute("SELECT 1 FROM users WHERE role = 'admin'").fetchone():
        conn.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
            ("System Administrator", "admin@revenue.gov.in", generate_password_hash("admin123"))
        )
    if not conn.execute("SELECT 1 FROM users WHERE role = 'officer'").fetchone():
        conn.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'officer')",
            ("Revenue Officer", "officer@revenue.gov.in", generate_password_hash("officer123"))
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_app_db()
    app.run(debug=True)
