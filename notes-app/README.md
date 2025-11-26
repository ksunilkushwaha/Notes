# Notes Hub — Deploy to Render (Free Tier)

This is a simple Flask app for uploading, viewing, and downloading student notes organized by subject.

## Files added for Render deployment
- `Procfile` — tells Render how to start the app with Gunicorn.
- `runtime.txt` — pins the Python runtime.
- `render.yaml` — optional Render service manifest for one-click deployment.
- Updated `requirements.txt` to include `gunicorn` and `python-dotenv`.
- `.gitignore` — ignore venv, db, and uploads.

## Quick setup (local)
1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run locally (development):

```powershell
python app.py
# or with gunicorn (simulate production):
C:\path\to\venv\Scripts\gunicorn app:app -b 0.0.0.0:8000
```

## Deploy to Render (Free Tier)
1. Push this repository to GitHub (or GitLab).
2. Go to https://render.com and create an account (free).
3. Create a new **Web Service** and connect your Git repo.
4. Set the following build and start commands if Render does not detect them automatically:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app -b 0.0.0.0:$PORT`

5. Choose the `Free` plan and deploy.

## Important Notes
- Uploaded files are saved to `static/uploads/<subject>/` and SQLite database `notes.db` is created in the project root. Render's file system is ephemeral across deploys — files will persist only while the instance is running. For production or long-term storage, use a managed object store (e.g., AWS S3 or Cloudinary) and a managed database (e.g., Render Postgres).

- Use environment variables for sensitive configuration. You can add environment variables on Render via the dashboard.

## Optional Improvements
- Switch to PostgreSQL and update `SQLALCHEMY_DATABASE_URI` using Render Postgres.
- Use S3/Cloudinary for file storage and serve files from CDN.
- Add user authentication if you want upload ownership and permissions.

If you want, I can:
- Create a simple integration to store uploads on S3/Cloudinary instead of local disk.
- Add a `Procfile` and `render.yaml` values customized with your repo name.
- Push a commit to your repo and trigger a Render deploy (if you authorize/connect).
