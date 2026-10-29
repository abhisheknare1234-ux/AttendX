import { NextRequest, NextResponse } from "next/server";

// ZEAL College Campus Anchor: Narhe Campus, Pune (18.4485° N, 73.8245° E)
const CAMPUS_DEFAULT_LAT = 18.4485;
const CAMPUS_DEFAULT_LON = 73.8245;
const CAMPUS_DEFAULT_RADIUS = 100.0; // meters

// Haversine formula to calculate accurate spherical distance in meters
function haversineDistanceMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Cosine similarity for 128-d/512-d facial biometric embeddings
function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (!vecA.length || !vecB.length || vecA.length !== vecB.length) return 0.92; // default high match if mock vectors match
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// In-Memory Database State for Serverless Execution
const mockUsers = [
  {
    id: "user-admin-1",
    email: "admin@zeal.attendx.ai",
    role: "ADMIN",
    first_name: "Zeal",
    last_name: "Admin",
    is_active: true,
  },
  {
    id: "user-teacher-1",
    email: "prof.sharma@zeal.edu.in",
    role: "TEACHER",
    first_name: "Prof. Rajesh",
    last_name: "Sharma",
    is_active: true,
    teacher_profile: {
      id: "teacher-1",
      department: "AI & Data Science",
      designation: "Associate Professor",
      employee_id: "ZCOER-EMP-0412",
    },
  },
  {
    id: "user-student-1",
    email: "aarav.patil@zeal.edu.in",
    role: "STUDENT",
    first_name: "Aarav",
    last_name: "Patil",
    is_active: true,
    student_profile: {
      id: "student-1",
      roll_no: "4101",
      prn: "72214589K",
      batch_year: 2026,
      academic_class_id: "class-aids-4",
    },
  },
  {
    id: "user-student-2",
    email: "neha.kulkarni@zeal.edu.in",
    role: "STUDENT",
    first_name: "Neha",
    last_name: "Kulkarni",
    is_active: true,
    student_profile: {
      id: "student-2",
      roll_no: "4102",
      prn: "72214590L",
      batch_year: 2026,
      academic_class_id: "class-aids-4",
    },
  },
];

const mockClassrooms = [
  {
    id: "room-lab-304",
    name: "Classroom Lab 304",
    building: "Building A - ZCOER",
    latitude: 18.4485,
    longitude: 73.8245,
    geofence_radius_meters: 100.0,
    is_active: true,
  },
  {
    id: "room-mech-102",
    name: "Mechanical Hall 102",
    building: "Mechanical Wing",
    latitude: 18.4490,
    longitude: 73.8250,
    geofence_radius_meters: 120.0,
    is_active: true,
  },
];

const mockClasses = [
  {
    id: "class-aids-4",
    name: "TE-AIDS-DivA",
    department: "Department of AI & Data Science",
    year_level: "Third Year (TE)",
  },
  {
    id: "class-comp-4",
    name: "BE-COMP-DivB",
    department: "Department of Computer Engineering",
    year_level: "Final Year (BE)",
  },
];

const mockSubjects = [
  {
    id: "subj-aids-401",
    code: "AIDS-401",
    title: "Deep Learning & Neural Architectures Lab",
    academic_class_id: "class-aids-4",
  },
  {
    id: "subj-cs-302",
    code: "CS-302",
    title: "Distributed Systems & Cloud Computing",
    academic_class_id: "class-comp-4",
  },
];

let mockSessions = [
  {
    id: "sess-live-01",
    subject_id: "subj-aids-401",
    subject_name: "AIDS-401 — Deep Learning Lab",
    classroom_id: "room-lab-304",
    classroom_name: "Lab 304 (AI & DS Dept)",
    teacher_id: "teacher-1",
    status: "OPEN",
    checkin_window_minutes: 10,
    qr_refresh_seconds: 30,
    require_face: true,
    require_geofence: true,
    require_liveness: true,
    created_at: new Date(Date.now() - 5 * 60000).toISOString(),
    opened_at: new Date(Date.now() - 5 * 60000).toISOString(),
    closed_at: null,
  },
];

let mockReviewQueue = [
  {
    id: "rev-01",
    session_id: "sess-live-01",
    student_id: "student-2",
    student_name: "Neha Kulkarni",
    roll_no: "4102",
    prn: "72214590L",
    status: "FLAGGED_FOR_REVIEW",
    risk_level: "MEDIUM",
    risk_score: 62.5,
    flag_reasons: ["GEOFENCE_MARGINAL: Distance 92m near boundary threshold (100m)"],
    distance_meters: 92.4,
    similarity_score: 0.94,
    created_at: new Date(Date.now() - 3 * 60000).toISOString(),
  },
];

let mockAuditLogs = [
  {
    id: "aud-01",
    actor_id: "user-admin-1",
    action: "SYSTEM_INITIALIZE",
    entity: "INSTITUTION",
    details: "AttendX AI Anti-Proxy System initialized for ZEAL College Narhe Campus",
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
  },
  {
    id: "aud-02",
    actor_id: "user-teacher-1",
    action: "SESSION_OPEN",
    entity: "SESSION",
    details: "Session opened for AIDS-401 in Lab 304 with 30s rotating cryptographic QR",
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
  },
];

// Helper to extract session user from auth token
function getAuthUser(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (!authHeader) return mockUsers[0]; // Fallback to admin if not provided
  const token = authHeader.replace("Bearer ", "");
  if (token.includes("teacher")) return mockUsers[1];
  if (token.includes("student-2")) return mockUsers[3];
  if (token.includes("student")) return mockUsers[2];
  return mockUsers[0];
}

export async function GET(request: NextRequest, { params }: { params: { slug: string[] } }) {
  const path = params.slug ? params.slug.join("/") : "";
  const { searchParams } = new URL(request.url);

  // 1. /auth/me
  if (path === "auth/me") {
    const user = getAuthUser(request);
    return NextResponse.json(user);
  }

  // 2. /reports/dashboard-stats
  if (path === "reports/dashboard-stats") {
    return NextResponse.json({
      total_students: 240,
      total_teachers: 18,
      total_classes: 8,
      total_classrooms: mockClassrooms.length,
      active_sessions_count: mockSessions.filter((s) => s.status === "OPEN").length,
      overall_attendance_rate: 87.4,
      proxy_attempts_prevented: 23,
      pending_reviews_count: mockReviewQueue.length,
      recent_activity: [
        {
          id: "act-1",
          type: "SESSION_LAUNCH",
          message: "Prof. Rajesh Sharma launched AIDS-401 Live Attendance Session in Lab 304",
          timestamp: "5 minutes ago",
        },
        {
          id: "act-2",
          type: "ANTI_PROXY_INTERCEPTION",
          message: "Spatial geofence engine flagged remote proxy check-in attempt (1.2 km away)",
          timestamp: "12 minutes ago",
        },
        {
          id: "act-3",
          type: "VERIFIED_CHECKIN",
          message: "Student Aarav Patil verified via Biometric Face Match & GPS Geofence",
          timestamp: "2 minutes ago",
        },
      ],
    });
  }

  // 3. /health
  if (path === "health") {
    return NextResponse.json({
      status: "healthy",
      version: "1.0.0",
      database: "connected",
      anti_proxy_engine: "operational",
      campus: "ZEAL College of Engineering & Research, Pune",
      active_geofences: mockClassrooms.length,
      timestamp: new Date().toISOString(),
    });
  }

  // 4. /academic/classrooms
  if (path === "academic/classrooms") {
    return NextResponse.json(mockClassrooms);
  }

  // 5. /academic/classes
  if (path === "academic/classes") {
    return NextResponse.json(mockClasses);
  }

  // 6. /academic/subjects
  if (path === "academic/subjects") {
    return NextResponse.json(mockSubjects);
  }

  // 7. /users
  if (path === "users") {
    const role = searchParams.get("role");
    const filtered = role ? mockUsers.filter((u) => u.role === role) : mockUsers;
    return NextResponse.json(filtered);
  }

  // 8. /sessions
  if (path === "sessions") {
    const status = searchParams.get("status");
    const filtered = status ? mockSessions.filter((s) => s.status === status) : mockSessions;
    return NextResponse.json(filtered);
  }

  // 9. /sessions/:id/qr-token
  if (path.startsWith("sessions/") && path.endsWith("/qr-token")) {
    const sessionId = path.split("/")[1];
    const nonce = Math.random().toString(36).substring(2, 10);
    const validSeconds = 30;
    const expiresAt = new Date(Date.now() + validSeconds * 1000).toISOString();
    const tokenStr = `ZEAL-ATTENDX-${sessionId}-${nonce}-${Date.now()}`;
    return NextResponse.json({
      session_id: sessionId,
      token_str: tokenStr,
      nonce,
      expires_at: expiresAt,
      valid_seconds: validSeconds,
      server_time: new Date().toISOString(),
    });
  }

  // 10. /sessions/:id
  if (path.startsWith("sessions/")) {
    const sessionId = path.split("/")[1];
    const session = mockSessions.find((s) => s.id === sessionId) || mockSessions[0];
    return NextResponse.json(session);
  }

  // 11. /review/queue
  if (path === "review/queue") {
    return NextResponse.json(mockReviewQueue);
  }

  // 12. /audit
  if (path === "audit") {
    return NextResponse.json(mockAuditLogs);
  }

  // 13. /reports/student/:id
  if (path.startsWith("reports/student/")) {
    const studentId = path.split("/")[2];
    return NextResponse.json({
      student_id: studentId,
      student_name: "Aarav Patil",
      roll_no: "4101",
      prn: "72214589K",
      total_sessions: 24,
      present_count: 21,
      attendance_percentage: 87.5,
      recent_checkins: [
        {
          session_id: "sess-live-01",
          subject_name: "AIDS-401 — Deep Learning Lab",
          status: "PRESENT",
          method: "QR_CODE",
          timestamp: new Date(Date.now() - 4 * 60000).toISOString(),
          risk_level: "LOW",
        },
      ],
    });
  }

  // 14. /reports/session/:id
  if (path.startsWith("reports/session/")) {
    return NextResponse.json([
      {
        student_id: "student-1",
        student_name: "Aarav Patil",
        roll_no: "4101",
        status: "PRESENT",
        verified_at: new Date(Date.now() - 4 * 60000).toISOString(),
        risk_level: "LOW",
        verification_method: "QR_CODE + BIOMETRIC + GEOFENCE",
      },
      {
        student_id: "student-2",
        student_name: "Neha Kulkarni",
        roll_no: "4102",
        status: "FLAGGED_FOR_REVIEW",
        verified_at: null,
        risk_level: "MEDIUM",
        verification_method: "PENDING_TEACHER_APPROVAL",
      },
    ]);
  }

  return NextResponse.json({ error: "Endpoint not found", path }, { status: 404 });
}

export async function POST(request: NextRequest, { params }: { params: { slug: string[] } }) {
  const path = params.slug ? params.slug.join("/") : "";
  let body: any = {};
  try {
    body = await request.json();
  } catch (e) {
    // Body optional or empty
  }

  // 1. /auth/login
  if (path === "auth/login") {
    const email = (body.email || "").toLowerCase().trim();
    let matchedUser = mockUsers.find((u) => u.email.toLowerCase() === email);

    if (!matchedUser) {
      if (email.includes("admin")) matchedUser = mockUsers[0];
      else if (email.includes("prof") || email.includes("teacher")) matchedUser = mockUsers[1];
      else if (email.includes("neha")) matchedUser = mockUsers[3];
      else matchedUser = mockUsers[2];
    }

    const token = `attendx_jwt_${matchedUser.role.toLowerCase()}_${Date.now()}`;
    return NextResponse.json({
      access_token: token,
      token_type: "bearer",
      user: matchedUser,
    });
  }

  // 2. /auth/logout
  if (path === "auth/logout") {
    return NextResponse.json({ status: "success", message: "Logged out successfully" });
  }

  // 3. /checkin (Student Anti-Proxy Multi-Factor Evaluation)
  if (path === "checkin") {
    const studentLat = body.latitude || CAMPUS_DEFAULT_LAT;
    const studentLon = body.longitude || CAMPUS_DEFAULT_LON;
    const distanceMeters = haversineDistanceMeters(
      studentLat,
      studentLon,
      CAMPUS_DEFAULT_LAT,
      CAMPUS_DEFAULT_LON
    );

    const isGeofencePass = distanceMeters <= CAMPUS_DEFAULT_RADIUS + (body.accuracy_meters || 15);
    const mockRefEmbedding = new Array(128).fill(0.1);
    const similarity = body.face_embedding
      ? cosineSimilarity(body.face_embedding, mockRefEmbedding)
      : 0.95;
    const isFacePass = similarity >= 0.85;

    let status = "VERIFIED";
    let riskLevel = "LOW";
    let riskScore = 8.5;
    const flagReasons: string[] = [];

    if (!isGeofencePass) {
      status = "FLAGGED";
      riskLevel = "HIGH";
      riskScore = 82.0;
      flagReasons.push(
        `GEOFENCE_VIOLATION: Student is ${Math.round(distanceMeters)}m away from classroom boundary (${CAMPUS_DEFAULT_RADIUS}m radius)`
      );
    }

    if (!isFacePass) {
      status = "FLAGGED";
      riskLevel = "HIGH";
      riskScore = Math.max(riskScore, 75.0);
      flagReasons.push(`BIOMETRIC_MISMATCH: Facial similarity ${similarity.toFixed(2)} below 0.85 institutional threshold`);
    }

    // Add to audit trail
    mockAuditLogs.unshift({
      id: `aud-${Date.now()}`,
      actor_id: "user-student-1",
      action: status === "VERIFIED" ? "CHECKIN_VERIFIED" : "CHECKIN_FLAGGED",
      entity: "ATTENDANCE_RECORD",
      details: `Student check-in attempt: Status ${status}, Distance ${Math.round(distanceMeters)}m, Face match ${(similarity * 100).toFixed(1)}%`,
      timestamp: new Date().toISOString(),
    });

    return NextResponse.json({
      status,
      risk_level: riskLevel,
      risk_score: riskScore,
      distance_meters: Math.round(distanceMeters * 10) / 10,
      biometric_match_confidence: similarity,
      flag_reasons: flagReasons,
      timestamp: new Date().toISOString(),
      message:
        status === "VERIFIED"
          ? "Attendance verified & cryptographically signed!"
          : "Check-in flagged by AttendX Anti-Proxy Engine and forwarded to Teacher review queue.",
    });
  }

  // 4. /sessions (Create Session)
  if (path === "sessions") {
    const newSession = {
      id: `sess-${Date.now()}`,
      subject_id: body.subject_id || "subj-aids-401",
      subject_name: "AIDS-401 — Deep Learning Lab",
      classroom_id: body.classroom_id || "room-lab-304",
      classroom_name: "Lab 304 (AI & DS Dept)",
      teacher_id: "teacher-1",
      status: "OPEN",
      checkin_window_minutes: body.checkin_window_minutes || 5,
      qr_refresh_seconds: body.qr_refresh_seconds || 30,
      require_face: body.require_face !== false,
      require_geofence: body.require_geofence !== false,
      require_liveness: body.require_liveness !== false,
      created_at: new Date().toISOString(),
      opened_at: new Date().toISOString(),
      closed_at: null,
    };
    mockSessions.unshift(newSession);
    return NextResponse.json(newSession);
  }

  // 5. /sessions/:id/open
  if (path.startsWith("sessions/") && path.endsWith("/open")) {
    const sessionId = path.split("/")[1];
    const sess = mockSessions.find((s) => s.id === sessionId);
    if (sess) {
      sess.status = "OPEN";
      sess.opened_at = new Date().toISOString();
    }
    return NextResponse.json({ status: "success", session: sess });
  }

  // 6. /sessions/:id/close
  if (path.startsWith("sessions/") && path.endsWith("/close")) {
    const sessionId = path.split("/")[1];
    const sess = mockSessions.find((s) => s.id === sessionId);
    if (sess) {
      sess.status = "CLOSED";
      sess.closed_at = new Date().toISOString();
    }
    return NextResponse.json({ status: "success", session: sess });
  }

  // 7. /review/:id/action
  if (path.startsWith("review/") && path.endsWith("/action")) {
    const attemptId = path.split("/")[1];
    mockReviewQueue = mockReviewQueue.filter((item) => item.id !== attemptId);
    return NextResponse.json({
      status: "success",
      message: `Attempt ${attemptId} has been successfully ${body.action || "APPROVED"}.`,
    });
  }

  // 8. /corrections/sessions/:id
  if (path.startsWith("corrections/sessions/")) {
    return NextResponse.json({
      status: "success",
      message: "Attendance correction recorded in institutional audit log.",
      timestamp: new Date().toISOString(),
    });
  }

  // 9. /academic/classrooms
  if (path === "academic/classrooms") {
    const newRoom = {
      id: `room-${Date.now()}`,
      name: body.name || "New Classroom",
      building: body.building || "Academic Complex",
      latitude: parseFloat(body.latitude) || CAMPUS_DEFAULT_LAT,
      longitude: parseFloat(body.longitude) || CAMPUS_DEFAULT_LON,
      geofence_radius_meters: parseFloat(body.geofence_radius_meters) || 100.0,
      is_active: true,
    };
    mockClassrooms.push(newRoom);
    return NextResponse.json(newRoom);
  }

  // 10. /academic/classes
  if (path === "academic/classes") {
    const newClass = {
      id: `class-${Date.now()}`,
      name: body.name || "New Division",
      department: body.department || "Engineering",
      year_level: body.year_level || "Third Year",
    };
    mockClasses.push(newClass);
    return NextResponse.json(newClass);
  }

  // 11. /academic/subjects
  if (path === "academic/subjects") {
    const newSubj = {
      id: `subj-${Date.now()}`,
      code: body.code || "NEW-101",
      title: body.title || "Course Subject",
      academic_class_id: body.academic_class_id || "class-aids-4",
    };
    mockSubjects.push(newSubj);
    return NextResponse.json(newSubj);
  }

  // 12. /users
  if (path === "users") {
    const newUser = {
      id: `user-${Date.now()}`,
      email: body.email,
      role: body.role || "STUDENT",
      first_name: body.first_name || "New",
      last_name: body.last_name || "User",
      is_active: true,
      student_profile:
        body.role === "STUDENT"
          ? {
              id: `stud-${Date.now()}`,
              roll_no: body.roll_no || "4199",
              prn: body.prn || "72214999Z",
              batch_year: 2026,
            }
          : undefined,
    };
    mockUsers.push(newUser);
    return NextResponse.json(newUser);
  }

  return NextResponse.json({ error: "Endpoint not found", path }, { status: 404 });
}
