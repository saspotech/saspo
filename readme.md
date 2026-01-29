# Saspo World Technologies - Web Platform

A high-performance, Flask-based Content Management System (CMS) designed for Immersive Tech Studios.

## 📋 Prerequisites

- **Python 3.10.11**
- **pip** (Python Package Manager)
- **Apache/Nginx** (Recommended for Production) or **cPanel**

## 🚀 Installation (Local)

1.  **Clone/Extract** the project files.
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    ```
3.  **Activate Environment**:
    - Windows: `venv\Scripts\activate`
    - Mac/Linux: `source venv/bin/activate`
4.  **Install Dependencies**:
    ```bash
    pip install Flask fpdf gunicorn werkzeug
    ```
5.  **Run Dev Server**:
    ```bash
    python app.py
    ```
    Access at `http://127.0.0.1:5000`

---

## ☁️ Deployment (cPanel / Shared Hosting)

This application is "Passenger-ready" for cPanel Python hosting.

1.  **Upload Files**: Upload all files to your domain directory (e.g., `public_html`).
2.  **Create Python App**:
    - Go to cPanel -> **Setup Python App**.
    - Select **Python 3.9+**.
    - Set App Root to your folder.
    - Set Application Startup File to `passenger_wsgi.py`.
3.  **Create `passenger_wsgi.py`**:
    Create a file named `passenger_wsgi.py` in the root folder with this content:
    ```python
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from app import app as application
    ```
4.  **Install Requirements**:
    - In the Python App dashboard, add `Flask`, `fpdf`, `gunicorn` to the configuration modules list and click **Add/Update**.
5.  **Restart**: Click the Restart button.

---

## 📂 Directory Structure

- **`app.py`**: The brain of the application. Handles routing, logic, and PDF generation.
- **`data.json`**: The database. Stores all text, links, and settings.
- **`links.json`**: Stores the list of YouTube video links.
- **`templates/`**: HTML files (`index.html`, `dashboard.html`, `login.html`).
- **`static/`**:
    - `img/`: Stores uploaded images.
    - `video/`: Stores background videos (e.g., `spaceship.mp4`).

---

## 🔐 Admin Access

- **Login URL:** `/login`
- **Default User:** `saspo`
- **Default Password:** `Password123*`

*⚠️ SECURITY WARNING: Please change these credentials in `app.py` (Lines 13-14) before going live.*

---

## 📱 Features

- **Flat-File CMS:** No SQL database required. Backup simply by downloading `data.json`.
- **Auto SEO:** Meta tags update automatically based on content.
- **PDF Manual:** Auto-generates an operations manual from the dashboard.
- **WhatsApp API:** Direct lead generation via URL redirection.