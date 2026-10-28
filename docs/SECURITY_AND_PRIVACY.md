# ATTENDX AI — Security & Privacy Architecture
**Institutional Standard**: Digital Personal Data Protection Act (DPDPA 2023, India) & Institutional Ethics  
**Target Context**: ZEAL College of Engineering & Research, Pune

---

## 1. Security Architecture & Controls

### 1.1 Password Hashing & Key Derivation
- Uses **Argon2id** (RFC 9106 recommended parameters: `time_cost=3`, `memory_cost=65536` [64 MiB], `parallelism=4`).
- Immune to GPU-accelerated dictionary attacks and time-memory trade-off attacks.

### 1.2 Authentication & Session Management
- Server-signed JSON Web Tokens (`HS256` in local/staging, `RS256` in production cluster).
- Transported over `HTTP-only`, `SameSite=Lax`, `Secure` cookies.
- Server maintains session state and checks account active status on every request.

### 1.3 Cryptographic Dynamic QR Codes
- Token structure: `ATX1.<session_id>.<nonce>.<expires_at>.<hmac_signature>`.
- Token signature: $\text{HMAC-SHA256}(K_{secret}, \text{session\_id} \parallel \text{nonce} \parallel \text{expires\_at})$.
- **Replay Resistance**: Nonce is checked against active session records. Expired or future-manipulated timestamps are rejected with a 2-second maximum clock skew allowance.
- **Photo-Sharing Defense**: Default 30-second token rotation ensures a captured photograph of a projected QR code is invalid within seconds.

### 1.4 Dynamic PIN Defense
- 6-digit numeric PINs derived from `secrets.randbelow` (CSPRNG).
- Stored as a salted hash: $\text{SHA256}(\text{session\_id} \parallel \text{pin})$.
- Enforced rate limiting: maximum 5 incorrect attempts before lockout.

### 1.5 CSV Formula Injection Defense (CWE-1236)
- Spreadsheet export sanitizes every cell starting with `=`, `+`, `-`, `@`, `\t`, or `\r` by prefixing a single quote `'`.

---

## 2. Privacy-by-Design & Data Minimization

1. **No Raw Biometric Storage**:
   - The platform **never stores raw facial imagery or video streams** on disk or in the database.
   - Only normalized mathematical feature embedding vectors (floating point arrays) are preserved for cosine similarity matching.
   - Embeddings cannot be reverse-engineered into high-fidelity human facial portraits.

2. **No Persistent Location Tracking**:
   - The platform never performs background or continuous student tracking.
   - Geolocation is captured strictly at the instant of check-in with explicit browser permission.
   - Only distance to classroom and accuracy margin are logged.

3. **Consent & Right to Rectification**:
   - Students can enroll and delete their biometric credentials upon graduation or institutional transfer.
   - Fallback PIN option is available for students with camera impairments or device privacy preferences.
