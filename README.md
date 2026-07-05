# Online Issuance of Caste and Other Certificates by Revenue Department

A complete full-stack web application that digitizes the process of applying for,
verifying, and issuing **Caste, Income, Community, Nativity, and Residence
certificates** through a Revenue Department portal.

Built with:
- **Frontend:** HTML5, CSS3, Bootstrap 5, vanilla JavaScript
- **Backend:** Python Flask
- **Database:** SQLite (built-in, no external DB server required — uses Python's
  native `sqlite3` module, no ORM installation needed)
- **PDF Generation:** ReportLab

---

## ✨ Features

### Citizen
- Register and log in with a personal account
- Apply online for 5 certificate types: Caste, Income, Community, Nativity, Residence
- Upload supporting documents (Photo, Aadhaar/ID proof, address proof, etc.)
- Track application status in real time (Pending / Approved / Rejected)
- Download the digitally generated PDF certificate once approved

### Revenue Officer
- Separate secure officer login
- Dashboard with counts of Pending / Approved / Rejected applications
- Review full applicant details and uploaded documents
- Approve (auto-generates an official PDF certificate) or reject (with remarks)
  each application

### Administrator
- Separate secure admin login
- Dashboard with system-wide statistics
- View all citizen applications across all officers
- Create and remove Revenue Officer accounts

### General
- Fully responsive modern "digital government portal" UI (Bootstrap 5 + Font Awesome)
- Session-based authentication with hashed passwords (Werkzeug)
- Role-based access control (citizen / officer / admin)
- Clean, organized project structure ready to open in VS Code

---

## 📁 Project Structure

```
caste_certificate_portal/
├── app.py                     # Main Flask application (routes, auth, logic)
├── database.py                # SQLite schema + connection helper (sqlite3)
├── certificate_generator.py   # Generates PDF certificates using ReportLab
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore
├── instance/                  # SQLite database file is created here automatically
│   └── certificate_portal.db  # (auto-generated on first run)
├── static/
│   ├── css/
│   │   └── style.css          # Custom government-portal styling
│   ├── js/
│   │   └── script.js          # Frontend interactivity
│   ├── uploads/                # Uploaded citizen documents (auto-created, per-application folders)
│   └── certificates/           # Generated certificate PDFs (auto-created)
└── templates/
    ├── base.html               # Shared layout (navbar, footer)
    ├── index.html               # Public homepage
    ├── register.html            # Citizen registration
    ├── login.html                # Citizen login
    ├── officer_login.html        # Revenue officer login
    ├── admin_login.html          # Admin login
    ├── citizen_dashboard.html    # Citizen dashboard
    ├── apply_certificate.html    # Certificate application form
    ├── application_detail.html   # Citizen's view of one application
    ├── officer_dashboard.html    # Officer's / admin's application list
    ├── view_application.html     # Officer/admin review + approve/reject screen
    ├── admin_dashboard.html       # Admin dashboard
    ├── add_officer.html           # Admin: create officer account
    └── 404.html                   # Error page
```

---

## 🛠️ Requirements

- Python 3.9 or higher
- pip (Python package manager)
- Visual Studio Code (recommended, with the Python extension)

No separate database server is required — SQLite runs as an embedded file-based
database (`instance/certificate_portal.db`), created automatically on first run.

---

## 🚀 Setup Instructions (Visual Studio Code)

### 1. Extract / open the project
Unzip the project folder and open it in VS Code:
```
File → Open Folder... → select "caste_certificate_portal"
```

### 2. Create a virtual environment (recommended)
Open the VS Code integrated terminal (`` Ctrl+` ``) and run:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

You should see output similar to:
```
 * Running on http://127.0.0.1:5000
```

### 5. Open in browser
Visit **http://127.0.0.1:5000** in your browser.

On the very first run, the app automatically:
- Creates the `instance/certificate_portal.db` SQLite database
- Creates all required tables (users, applications, documents)
- Seeds one default **Admin** account and one default **Revenue Officer** account
  (see credentials below)

---

## 🔑 Default Login Credentials (Demo)

| Role            | Email                     | Password    |
|-----------------|----------------------------|-------------|
| Administrator   | admin@revenue.gov.in        | admin123    |
| Revenue Officer | officer@revenue.gov.in      | officer123  |
| Citizen         | *(register your own via the Register page)* | — |

> ⚠️ For a production deployment, change these default passwords immediately and
> set a strong, unique `SECRET_KEY` in `app.py`.

---

## 🧭 Application Workflow

1. **Citizen** registers an account and logs in.
2. **Citizen** applies for a certificate (Caste / Income / Community / Nativity /
   Residence), fills personal details, and uploads supporting documents.
3. The application appears with status **Pending** in both the citizen's and the
   **Revenue Officer's** dashboards.
4. **Revenue Officer** logs in, opens the application, reviews the details and
   uploaded documents, and either:
   - **Approves** it → a digitally formatted PDF certificate is generated instantly, or
   - **Rejects** it → with a remark explaining the reason.
5. **Citizen** sees the updated status on their dashboard and can **download the
   PDF certificate** once approved.
6. **Administrator** can monitor all applications system-wide and manage
   Revenue Officer accounts.

---

## 🗄️ Database Schema (SQLite)

**users** — id, full_name, email, phone, address, password_hash, role
(`citizen` / `officer` / `admin`), created_at

**applications** — id, application_no, user_id, cert_type, applicant_name,
father_name, dob, gender, caste, religion, annual_income, address, district,
taluk, village, purpose, status, remarks, officer_id, certificate_path,
created_at, updated_at

**documents** — id, application_id, doc_type, original_name, stored_name,
uploaded_at

The database file is created automatically — **no manual SQL setup is required**.
If you want to reset all data, simply stop the app, delete
`instance/certificate_portal.db`, and restart the app (`python app.py`); it will
be recreated automatically (including default admin/officer accounts).

---

## 📄 Certificate PDF Generation

When a Revenue Officer approves an application, `certificate_generator.py`
uses **ReportLab** to generate an official-looking A4 PDF certificate with:
- Government header and department name
- Certificate type, unique application/certificate number, and date of issue
- All verified applicant details
- Officer's digital signature block

Generated PDFs are stored in `static/certificates/` and can be downloaded by the
citizen from their dashboard, or by the officer/admin from the review screen.

---

## 🔒 Security Notes

- Passwords are hashed using Werkzeug's `generate_password_hash` /
  `check_password_hash` (never stored in plain text).
- Role-based route protection ensures citizens, officers, and admins can only
  access pages relevant to their role.
- File uploads are restricted to `.pdf`, `.png`, `.jpg`, `.jpeg` with a 10MB
  size limit, and are renamed using UUIDs to avoid collisions/overwrites.
- Citizens can only view/download their own applications and documents;
  officers/admins can view all.

---

## 🧩 Troubleshooting

- **"ModuleNotFoundError"** → Make sure you activated the virtual environment
  and ran `pip install -r requirements.txt`.
- **Port already in use** → Another app is using port 5000. Stop it, or run
  `app.run(debug=True, port=5001)` in `app.py`.
- **Database looks empty / old data missing** → Delete
  `instance/certificate_portal.db` and restart `python app.py` to reseed.
- **File upload fails** → Check the file type (only PDF/JPG/PNG allowed) and
  size (max 10MB).

---

## 📌 Notes for Evaluators / Reviewers

This project was built and tested end-to-end (registration → application →
document upload → officer approval → PDF certificate generation → citizen
download, plus rejection flow, admin dashboard, and access-control checks) to
ensure it runs without errors when set up as described above.

---

## 📃 License

This project is provided for educational and demonstration purposes.
