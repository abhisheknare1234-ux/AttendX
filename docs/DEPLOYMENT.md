# ATTENDX AI — Production Deployment & Operations Guide
**Target Institution**: ZEAL College of Engineering & Research, Pune, Maharashtra

---

## 1. Local Development Quickstart

### Prerequisites
- Python 3.10+ (Tested on Python 3.14.0)
- Node.js 18+ (Tested on Node.js v24.22.1)
- Git

### Step 1: Clone & Virtual Environment
```bash
git clone <repo-url> attendx-ai
cd attendx-ai
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

### Step 2: Install Backend Dependencies
```bash
pip install -r apps/api/requirements.txt
```

### Step 3: Run Database Migrations
```bash
alembic upgrade head
```

### Step 4: Run Automated Tests
```bash
pytest -v apps/api/tests
```

### Step 5: Install Frontend & Build
```bash
cd apps/web
npm install
npm run build
```

### Step 6: Start Application Services
- **Backend API Server**:
  ```bash
  .\.venv\Scripts\uvicorn apps.api.src.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Frontend Web Dashboard**:
  ```bash
  cd apps/web
  npm run dev
  ```
  Open `http://localhost:3000` in your browser.

---

## 2. Docker Compose Production Deployment

```bash
docker-compose up --build -d
```
Services launched:
- `attendx-postgres`: PostgreSQL 16 Alpine on port 5432 with health check.
- `attendx-api`: FastAPI backend on port 8000 with production health check.
- `attendx-web`: Next.js production build on port 3000.

---

## 3. Production Hardening Checklist

1. [x] **High-Entropy Secret Key**: Set `SECRET_KEY` to a random 64-character secret.
2. [x] **PostgreSQL Enforcement**: Production mode rejects SQLite connections automatically.
3. [x] **Secure HTTPS Cookies**: Ensure `secure=True` on session cookies behind an SSL reverse proxy (e.g. Nginx, Caddy, or AWS ALB).
4. [x] **Firewall & Geofence Policy**: Ensure classroom anchor coordinates match physical institutional buildings.
5. [x] **Database Automated Backups**: Schedule daily `pg_dump` snapshots to institutional cold storage.
