# LabTracker

Internal lab asset tracking tool for testers, stations, boards, and chips.

Built with Django, Google SSO, PostgreSQL, and deployed on Render.

---

## Features

- **Asset tracking** — testers, stations, boards, chips, and more
- **Check-in / Check-out** — with full audit history per asset
- **Asset relationships** — attach chips to boards, boards to stations, etc.
- **Global search** — filter by name, tag, location, serial number
- **Status tracking** — available / in-use / repair / retired
- **Admin interface** — Django admin for adding and editing assets
- **Google SSO** — secure login for internal users

---

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/labtracker.git
cd labtracker

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `SECRET_KEY` | Generate at https://djecrety.ir |
| `GOOGLE_CLIENT_ID` | Google Cloud Console (see below) |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console (see below) |

### 3. Google OAuth2 Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable **Google+ API** or **People API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs:
   - `http://127.0.0.1:8000/auth/complete/google-oauth2/` (local)
   - `https://your-app.onrender.com/auth/complete/google-oauth2/` (production)
7. Copy **Client ID** and **Client Secret** into `.env`

### 4. Run migrations and create superuser

```bash
python manage.py makemigrations tracker
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` — you'll be redirected to the login page.

---

## Deploy to Render

### Option A — render.yaml (recommended)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — Render will detect `render.yaml` automatically
4. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` as environment variables
5. Update `ALLOWED_HOSTS` in render.yaml to your actual Render URL

### Option B — Manual setup

1. Push repo to GitHub
2. Render → New → **Web Service** → connect repo
3. **Build command:**
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
4. **Start command:** `gunicorn labtracker.wsgi`
5. Add environment variables:
   - `SECRET_KEY`
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-app.onrender.com`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
6. Add a **PostgreSQL** database — Render sets `DATABASE_URL` automatically
7. Update Google OAuth redirect URI to your Render URL

---

## Project Structure

```
labtracker/
├── labtracker/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tracker/             # Main app
│   ├── models.py        # Asset, AssetRelationship, AuditLog
│   ├── views.py         # All core workflows
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── templates/
│   └── tracker/         # All HTML templates
├── static/
│   └── css/app.css      # Full stylesheet
├── requirements.txt
├── render.yaml
└── manage.py
```

## Data Models

| Model | Description |
|---|---|
| `Asset` | Any lab item with type, status, location, tag |
| `AssetRelationship` | Parent-child links between assets |
| `AuditLog` | Immutable history of every action |

---

## Usage

| URL | Description |
|---|---|
| `/` | Dashboard with stats and recent activity |
| `/assets/` | Full asset list with search and filters |
| `/assets/new/` | Add a new asset |
| `/assets/<id>/` | Asset detail, relationships, audit log |
| `/audit/` | Full audit log across all assets |
| `/admin/` | Django admin (staff only) |
