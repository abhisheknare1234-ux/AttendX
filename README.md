# ATTENDX AI — Smart Attendance & Anti-Proxy Verification System
**Institutional Context**: ZEAL College of Engineering & Research (ZCOER), Narhe, Pune, Maharashtra, India  
**Target Department**: Department of Artificial Intelligence & Data Science (AIDS)  
**Engineering Class**: Institutional-Grade Verification Platform (Dedicated Attendance System — *Not an ERP*)

---

## 1. Executive Summary

**AttendX AI** is an independent, server-authoritative attendance verification platform designed to permanently eliminate attendance fraud (proxy check-ins) in academic institutions. 

Unlike conventional QR scanners or Bluetooth beacons that can be readily fooled by sharing screenshots or spoofing coordinates, AttendX AI establishes an **Explainable Multi-Factor Evidence Fusion Pipeline**:

1. **Dynamic Cryptographic QR Tokens**: Short-lived (30-second rotation), HMAC-SHA256 signed, synchronized to server time, and non-replayable.
2. **CSPRNG Temporary Fallback PINs**: Dynamic 6-digit numeric PINs with salted SHA-256 hashes and 5-attempt rate-limit lockouts.
3. **Classroom GPS Geofencing**: WGS-84 Haversine spherical distance calculation relative to institutional classroom anchors (e.g., ZEAL Building A - Lab 304).
4. **Live Facial Biometrics**: 32-to-128-dimensional normalized facial feature vectors evaluated against enrolled templates via Cosine Similarity ($\ge 0.75$).
5. **Anti-Spoofing & Liveness Analysis**: Passive challenge verification protecting against print and replay presentation attacks.
6. **Explainable AI-Assisted Risk Engine**: Deterministic evidence fusion translating all factor states into auditable outcomes:
   - `ACCEPTED`: Verified present and written to official ledger.
   - `REQUIRES_REVIEW`: Sent to Teacher Review Queue due to environmental conditions (e.g. indoor GPS attenuation).
   - `REJECTED`: Invariant violation (expired QR, duplicate attempt, student not enrolled, face mismatch).
7. **Controlled Teacher Corrections & Audit Ledger**: Immutable history recording acting faculty member, prior state, new state, and mandatory justification.

---

## 2. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons, `qrcode.react`.
- **Backend**: Python 3.14 / FastAPI, Pydantic 2.x, SQLAlchemy 2.0 (Declarative Mappings), Alembic Migrations.
- **Security**: Argon2id password hashing, HTTP-Only SameSite JWT cookies, HMAC-SHA256 token signing.
- **Database**: PostgreSQL 16 (Production Docker Compose) / SQLite3 (Zero-setup local development).
- **Testing**: Pytest automated test suite (27 unit, service, security, and full API integration tests).

---

## 3. Quickstart & Local Installation

### 3.1 Backend Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux / macOS

# 2. Install backend dependencies
pip install -r apps/api/requirements.txt

# 3. Apply Alembic migrations
alembic upgrade head

# 4. Bootstrap demonstration fixtures
python scripts/bootstrap.py

# 5. Run automated test suite
pytest -v apps/api/tests

# 6. Start FastAPI server (Port 8000)
python -m uvicorn apps.api.src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.2 Frontend Setup
```bash
cd apps/web

# 1. Install dependencies
npm install

# 2. Build for production (verifies types & bundles)
npm run build

# 3. Start development server (Port 3000)
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## 4. Evaluation Credentials

The bootstrap script provisions the following accounts:

| Role | Email | Password | Scope |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@zeal.attendx.ai` | `ZealAdmin@2026Secure!` | User provisioning, geofence setup, classes, audit logs |
| **Faculty (Teacher)** | `prof.sharma@zeal.edu.in` | `TeacherPassword123!` | Session launch, live dynamic QR stream, review queue, CSV export |
| **Student 1** | `aarav.patil@zeal.edu.in` | `StudentPassword123!` | TE-AIDS-DivA, enrolled biometrics, live check-in |
| **Student 2** | `neha.kulkarni@zeal.edu.in` | `StudentPassword123!` | TE-AIDS-DivA, test review queue triage |

---

## 5. Project Architecture & Directory Structure

```text
attendx-ai/
├── apps/
│   ├── api/                     # FastAPI Backend Application
│   │   ├── src/
│   │   │   ├── core/            # Config, Database, Argon2/HMAC Security, Audit
│   │   │   ├── models/          # SQLAlchemy 2.0 Entities (User, Academic, Attendance)
│   │   │   ├── schemas/         # Pydantic Request & Response Contracts
│   │   │   ├── services/        # Geofence, Biometrics, QR/PIN, Risk Engine
│   │   │   └── api/v1/          # Endpoints (auth, users, sessions, checkin, review, reports)
│   │   └── tests/               # 27 Unit and API Integration Tests
│   └── web/                     # Next.js 14 App Router Frontend
│       └── src/
│           ├── app/             # Split-screen Auth page, Dashboard Layout & Pages
│           ├── components/      # Admin, Teacher, and Student Dashboards
│           └── lib/             # Type-safe API Client
├── database/
│   └── migrations/              # Alembic Versioned Migrations
├── docs/                        # Complete Institutional Engineering Documentation
│   ├── ARCHITECTURE.md          # Architectural blueprints and data flows
│   ├── DATABASE_DESIGN.md       # ERD, entities, constraints, and audit tables
│   ├── API_CONTRACT.md          # OpenAPI specifications and payloads
│   ├── SECURITY_AND_PRIVACY.md  # DPDPA 2023 compliance and cryptographic controls
│   ├── THREAT_MODEL.md          # STRIDE vulnerability matrix and mitigations
│   ├── TEST_PLAN.md             # Test register and validation outcomes
│   ├── KNOWN_LIMITATIONS.md     # Defensibility register and physical factor constraints
│   ├── IMPLEMENTATION_ROADMAP.md# 10 Milestones tracking
│   └── DEPLOYMENT.md            # Production deployment and Docker Compose guide
├── scripts/
│   └── bootstrap.py             # Institutional seed and demo fixture generator
├── docker-compose.yml           # PostgreSQL + API + Web container orchestration
├── pytest.ini                   # Pytest test discovery configuration
└── README.md                    # System documentation
```

---

## 6. Security & Data Protection Compliance

- **DPDPA 2023 (India) Compliance**: Raw facial photographs and videos are never retained. Only mathematical embedding vectors are preserved.
- **Zero Background Tracking**: Geolocation is polled exclusively at the instant of student check-in with explicit user approval.
- **CWE-1236 Defense**: CSV exports escape formula characters (`=`, `+`, `-`, `@`) to protect faculty spreadsheet software.
