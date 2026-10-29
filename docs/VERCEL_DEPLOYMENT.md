# ATTENDX AI — Vercel Deployment Guide
**Institutional Context**: ZEAL College of Engineering & Research, Pune

This guide explains how to deploy **AttendX AI** on Vercel.

---

## 1. Architectural Overview for Vercel

AttendX AI is a modern full-stack application consisting of:
1. **Frontend**: Next.js 14 App Router, React 18, Tailwind CSS (located in `apps/web`).
2. **Backend**: Python 3.14 FastAPI, SQLAlchemy 2.0, Alembic, Pydantic (located in `apps/api`).
3. **Database**: PostgreSQL (Production) / SQLite (Local).

Because Vercel is primarily optimized for Next.js and serverless functions, you have two proven deployment paths:

| Deployment Path | Frontend | Backend | Database | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Path A (Recommended SaaS Architecture)** | Vercel Edge Network | Render / Railway / Fly.io / Koyeb | Neon / Supabase / Render Postgres | Long-running institutional pilots, live dynamic QR streams, production reliability |
| **Path B (Unified Vercel Serverless)** | Vercel | Vercel Python Serverless (`api/index.py`) | Neon / Supabase Serverless Postgres | Single-click demo deployment entirely hosted within Vercel |

---

## 2. Path A: Deploy Next.js on Vercel + Backend on Cloud (Recommended)

This gives you the best performance: Next.js frontend deployed to Vercel's global CDN, communicating with a persistent FastAPI backend.

### Step 1: Deploy Backend (Render / Railway / Koyeb)
1. Push your Git repository to GitHub.
2. In [Render](https://render.com) or [Railway](https://railway.app):
   - Choose **New Web Service** -> Connect your GitHub repo.
   - **Root Directory**: `.` (or `apps/api`)
   - **Build Command**: `pip install -r apps/api/requirements.txt`
   - **Start Command**: `python -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `SECRET_KEY`: High-entropy 64-char string (e.g. generated via `openssl rand -hex 32`)
     - `ENVIRONMENT`: `production`
     - `DATABASE_URL`: Your hosted PostgreSQL connection string (e.g. from Neon.tech, Supabase, or Render Postgres)
3. Copy your live backend URL (e.g. `https://attendx-api.onrender.com`).

### Step 2: Deploy Frontend on Vercel
1. Log in to [Vercel](https://vercel.com) and click **"Add New..." -> "Project"**.
2. Select your GitHub repository and click **Import**.
3. Under **Configure Project**:
   - **Project Name**: `attendx-ai`
   - **Framework Preset**: **Next.js**
   - **Root Directory**: Click **Edit** and select **`apps/web`**.
4. Open **Environment Variables** and add:
   - `API_BACKEND_URL`: `https://attendx-api.onrender.com` (your hosted backend URL from Step 1)
   - `NEXT_PUBLIC_API_URL`: `/api/v1` (uses the built-in Next.js reverse-proxy rewrite to eliminate CORS issues)
5. Click **Deploy**.
6. Vercel will build and deploy your application in under 60 seconds! Your site will be live at `https://attendx-ai.vercel.app`.

---

## 3. Path B: Unified Full-Stack Deployment on Vercel

If you want the entire system (Next.js + Python FastAPI) hosted in a single Vercel project, AttendX AI includes pre-configured Vercel serverless entry points:
- [**`vercel.json`**](file:///d:/P123/vercel.json): Configured with URL rewrites directing `/api/v1/*` to the Python serverless function.
- [**`api/index.py`**](file:///d:/P123/api/index.py): Vercel Serverless Function entry point exporting the ASGI FastAPI application.
- [**`requirements.txt`**](file:///d:/P123/requirements.txt): Root package manifest for Vercel's `@vercel/python` builder.

### Prerequisites for Serverless Python on Vercel:
> [!IMPORTANT]
> Because Vercel serverless functions have an ephemeral (temporary) file system, you **must use a cloud PostgreSQL database** (such as [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com) — both offer free tiers). If you do not provide a PostgreSQL `DATABASE_URL`, data saved to local SQLite will not persist across serverless cold starts.

### Steps to Deploy via Vercel Dashboard:
1. Create a free PostgreSQL database on [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com).
2. Push your repository to GitHub.
3. In Vercel, import the repository with **Root Directory** set to `.`.
4. In **Environment Variables**, add:
   ```env
   DATABASE_URL=postgresql+psycopg2://user:password@ep-host.neon.tech/attendx_db?sslmode=require
   SECRET_KEY=your_secure_random_64_character_hex_key_here
   ENVIRONMENT=production
   INITIAL_ADMIN_EMAIL=admin@zeal.attendx.ai
   INITIAL_ADMIN_PASSWORD=YourSecurePassword2026!
   ```
5. Click **Deploy**.

---

## 4. Deploying via Vercel CLI (Optional)

You can also deploy directly from your local terminal:

```powershell
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy frontend
cd apps/web
vercel
```

Follow the interactive prompts:
- *Set up and deploy?* **Y**
- *Which scope?* (Select your account)
- *Link to existing project?* **N**
- *Project name?* `attendx-ai`
- *In which directory is your code located?* `./`

When prompted, set environment variable:
```powershell
vercel env add API_BACKEND_URL
```

---

## 5. Post-Deployment Institutional Verification Checklist

After deploying on Vercel:
1. **Health Check**: Open `https://your-app.vercel.app/api/v1/health` in your browser. Confirm status is `"healthy"`.
2. **Administrator Login**: Sign in at `https://your-app.vercel.app` using `admin@zeal.attendx.ai`.
3. **Faculty Check**: Launch a test session and verify dynamic QR rendering with 30s countdown.
4. **Student Check**: Verify geolocation permission prompt and camera preview for facial evidence.
5. **HTTPS Cookies**: Confirm browser inspect tools show `attendx_token` stored as a secure HTTP-only cookie.

