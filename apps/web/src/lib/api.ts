const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = typeof window !== "undefined" ? localStorage.getItem("attendx_token") : null;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const res = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errMessage = `HTTP error ${res.status}`;
      try {
        const errJson = await res.json();
        errMessage = errJson.detail || errMessage;
      } catch (e) {
        // Fallback
      }
      throw new Error(errMessage);
    }

    return res.json() as Promise<T>;
  }

  // Auth
  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (typeof window !== "undefined") {
      localStorage.setItem("attendx_token", data.access_token);
      localStorage.setItem("attendx_user", JSON.stringify(data.user));
    }
    return data;
  }

  async logout() {
    try {
      await this.request("/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignore
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("attendx_token");
        localStorage.removeItem("attendx_user");
      }
    }
  }

  async getMe() {
    return this.request<any>("/auth/me");
  }

  // Dashboard & Metrics
  async getDashboardStats() {
    return this.request<any>("/reports/dashboard-stats");
  }

  // Sessions
  async getSessions(status?: string) {
    const qs = status ? `?status=${status}` : "";
    return this.request<any[]>(`/sessions${qs}`);
  }

  async getSessionDetails(id: string) {
    return this.request<any>(`/sessions/${id}`);
  }

  async createSession(data: {
    subject_id: string;
    classroom_id: string;
    checkin_window_minutes: number;
    qr_refresh_seconds: number;
    require_face: boolean;
    require_geofence: boolean;
    require_liveness: boolean;
  }) {
    return this.request<any>("/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async openSession(id: string) {
    return this.request<any>(`/sessions/${id}/open`, { method: "POST" });
  }

  async closeSession(id: string) {
    return this.request<any>(`/sessions/${id}/close`, { method: "POST" });
  }

  async getQRToken(sessionId: string) {
    return this.request<{
      session_id: string;
      token_str: string;
      nonce: string;
      expires_at: string;
      valid_seconds: number;
      server_time: string;
    }>(`/sessions/${sessionId}/qr-token`);
  }

  // Student Check-In
  async submitCheckIn(data: {
    session_id: string;
    method: "QR_CODE" | "PIN_FALLBACK";
    qr_token?: string;
    pin?: string;
    latitude?: number;
    longitude?: number;
    accuracy_meters?: number;
    face_embedding?: number[];
    face_capture_quality?: number;
    liveness_confirmed?: boolean;
  }) {
    return this.request<any>("/checkin", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Teacher Review
  async getReviewQueue(sessionId?: string) {
    const qs = sessionId ? `?session_id=${sessionId}` : "";
    return this.request<any[]>(`/review/queue${qs}`);
  }

  async processReviewAction(attemptId: string, action: "APPROVE" | "REJECT", reason: string) {
    return this.request<any>(`/review/${attemptId}/action`, {
      method: "POST",
      body: JSON.stringify({ action, reason }),
    });
  }

  // Attendance Corrections
  async submitCorrection(sessionId: string, studentId: string, newStatus: string, reason: string) {
    return this.request<any>(`/corrections/sessions/${sessionId}`, {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, new_status: newStatus, reason }),
    });
  }

  async getSessionCorrections(sessionId: string) {
    return this.request<any[]>(`/corrections/sessions/${sessionId}`);
  }

  // Reports
  async getSessionRoster(sessionId: string) {
    return this.request<any[]>(`/reports/session/${sessionId}`);
  }

  async getStudentSummary(studentId: string) {
    return this.request<any>(`/reports/student/${studentId}`);
  }

  // Academics
  async getClassrooms() {
    return this.request<any[]>("/academic/classrooms");
  }

  async createClassroom(data: any) {
    return this.request<any>("/academic/classrooms", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getClasses() {
    return this.request<any[]>("/academic/classes");
  }

  async createClass(data: any) {
    return this.request<any>("/academic/classes", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getSubjects(classId?: string) {
    const qs = classId ? `?class_id=${classId}` : "";
    return this.request<any[]>(`/academic/subjects${qs}`);
  }

  async createSubject(data: any) {
    return this.request<any>("/academic/subjects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Users & Biometrics
  async getUsers(role?: string) {
    const qs = role ? `?role=${role}` : "";
    return this.request<any[]>(`/users${qs}`);
  }

  async provisionUser(data: any) {
    return this.request<any>("/users", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async enrollBiometric(studentId: string, referenceVector: number[]) {
    return this.request<any>(`/users/${studentId}/enroll-biometric`, {
      method: "POST",
      body: JSON.stringify({ reference_embedding: referenceVector }),
    });
  }

  // Audit Logs
  async getAuditLogs(action?: string) {
    const qs = action ? `?action=${action}` : "";
    return this.request<any[]>(`/audit${qs}`);
  }

  // Health
  async getHealth() {
    return this.request<any>("/health");
  }
}

export const api = new ApiClient();

