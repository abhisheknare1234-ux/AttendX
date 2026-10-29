"use client";

import React, { useState, useEffect } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  Clock,
  QrCode,
  Users,
  CheckCircle,
  AlertTriangle,
  Play,
  Square,
  FileSpreadsheet,
  RefreshCw,
  Edit3,
  ShieldAlert,
  ChevronRight,
  UserCheck,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";

export default function TeacherDashboard({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState<"sessions" | "review" | "corrections">("sessions");
  const [sessions, setSessions] = useState<any[]>([]);
  const [reviewQueue, setReviewQueue] = useState<any[]>([]);
  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // New Session Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedClassroomId, setSelectedClassroomId] = useState("");
  const [checkinWindow, setCheckinWindow] = useState(5);
  const [qrRefreshSeconds, setQrRefreshSeconds] = useState(30);
  const [requireFace, setRequireFace] = useState(true);
  const [requireGeo, setRequireGeo] = useState(true);

  // Live QR Modal State
  const [activeSession, setActiveSession] = useState<any>(null);
  const [liveQRToken, setLiveQRToken] = useState<string | null>(null);
  const [liveExpiresAt, setLiveExpiresAt] = useState<string | null>(null);
  const [secondsRemaining, setSecondsRemaining] = useState(30);

  // Review Action Modal State
  const [reviewModalItem, setReviewModalItem] = useState<any>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVE" | "REJECT">("APPROVE");
  const [reviewReason, setReviewReason] = useState("");

  // Correction Modal State
  const [isCorrectionModalOpen, setIsCorrectionModalOpen] = useState(false);
  const [correctionSessionId, setCorrectionSessionId] = useState("");
  const [sessionRoster, setSessionRoster] = useState<any[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [newStatus, setNewStatus] = useState("PRESENT");
  const [correctionReason, setCorrectionReason] = useState("");

  const loadTeacherData = async () => {
    setLoading(true);
    try {
      const [sess, queue, rooms, subjs] = await Promise.all([
        api.getSessions().catch(() => []),
        api.getReviewQueue().catch(() => []),
        api.getClassrooms().catch(() => []),
        api.getSubjects().catch(() => []),
      ]);
      setSessions(sess);
      setReviewQueue(queue);
      setClassrooms(rooms);
      setSubjects(subjs);
      if (rooms.length > 0 && !selectedClassroomId) setSelectedClassroomId(rooms[0].id);
      if (subjs.length > 0 && !selectedSubjectId) setSelectedSubjectId(subjs[0].id);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeacherData();
  }, []);

  // Live QR Stream Countdown & Auto-Refresh
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (activeSession && activeSession.status === "OPEN") {
      const fetchQR = async () => {
        try {
          const res = await api.getQRToken(activeSession.id);
          setLiveQRToken(res.token_str);
          setLiveExpiresAt(res.expires_at);
          setSecondsRemaining(res.valid_seconds);
        } catch (err: any) {
          console.error("QR stream error", err);
        }
      };

      fetchQR();
      const interval = setInterval(fetchQR, (activeSession.qr_refresh_seconds || 30) * 1000);

      const secCountdown = setInterval(() => {
        setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : activeSession.qr_refresh_seconds || 30));
      }, 1000);

      return () => {
        clearInterval(interval);
        clearInterval(secCountdown);
      };
    }
  }, [activeSession]);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newSess = await api.createSession({
        subject_id: selectedSubjectId,
        classroom_id: selectedClassroomId,
        checkin_window_minutes: Number(checkinWindow),
        qr_refresh_seconds: Number(qrRefreshSeconds),
        require_face: requireFace,
        require_geofence: requireGeo,
        require_liveness: false,
      });
      setIsCreateModalOpen(false);
      setMessage({ text: "Attendance session created in DRAFT state.", type: "success" });
      loadTeacherData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const handleOpenSession = async (sessId: string) => {
    try {
      const opened = await api.openSession(sessId);
      setMessage({ text: "Attendance check-in window is now OPEN.", type: "success" });
      setActiveSession(opened);
      loadTeacherData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const handleCloseSession = async (sessId: string) => {
    try {
      await api.closeSession(sessId);
      setMessage({ text: "Session officially CLOSED. Ledger locked.", type: "success" });
      if (activeSession?.id === sessId) {
        setActiveSession(null);
        setLiveQRToken(null);
      }
      loadTeacherData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const handleReviewAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewModalItem) return;
    try {
      await api.processReviewAction(reviewModalItem.attempt_id, reviewAction, reviewReason);
      setMessage({ text: `Check-in ${reviewAction}ED with documented justification.`, type: "success" });
      setReviewModalItem(null);
      setReviewReason("");
      loadTeacherData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const openCorrectionModalForSession = async (sessId: string) => {
    setCorrectionSessionId(sessId);
    try {
      const roster = await api.getSessionRoster(sessId);
      setSessionRoster(roster);
      if (roster.length > 0) setSelectedStudentId(roster[0].student_id);
      setIsCorrectionModalOpen(true);
    } catch (err: any) {
      setMessage({ text: "Failed to load session roster.", type: "error" });
    }
  };

  const handleApplyCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.submitCorrection(correctionSessionId, selectedStudentId, newStatus, correctionReason);
      setMessage({ text: "Manual attendance correction applied and audited.", type: "success" });
      setIsCorrectionModalOpen(false);
      setCorrectionReason("");
      loadTeacherData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-[14px] border border-[#E5EAF1] p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-[#202938]">Faculty Verification Workspace</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-[#2864E8]">
              Assigned Faculty
            </span>
          </div>
          <p className="text-xs text-[#728096] mt-1">
            Prof. {user.first_name} {user.last_name} &bull; Dept of AI & Data Science
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center space-x-2 text-xs font-semibold text-white bg-[#2864E8] hover:bg-[#1F55C7] px-4 py-2.5 rounded-[9px] transition-colors shadow-sm"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Launch Attendance Session</span>
          </button>
          <button
            onClick={loadTeacherData}
            disabled={loading}
            className="p-2.5 text-[#728096] hover:text-[#202938] border border-[#E5EAF1] rounded-[9px] hover:bg-[#F7F9FC]"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-[12px] text-xs font-medium flex items-center space-x-2 border ${
            message.type === "success"
              ? "bg-green-50 text-green-800 border-green-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {message.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[#E5EAF1] space-x-6 text-sm">
        <button
          onClick={() => setActiveTab("sessions")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "sessions"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Attendance Sessions ({sessions.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("review")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "review"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Review Queue</span>
          {reviewQueue.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-white">
              {reviewQueue.length}
            </span>
          )}
        </button>
      </div>

      {/* SESSIONS TAB */}
      {activeTab === "sessions" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {sessions.length === 0 ? (
              <div className="bg-white p-8 rounded-[14px] border border-[#E5EAF1] text-center text-xs text-[#728096]">
                No attendance sessions created yet. Click "Launch Attendance Session" to conduct verification.
              </div>
            ) : (
              sessions.map((sess) => (
                <div
                  key={sess.id}
                  className="bg-white p-5 rounded-[14px] border border-[#E5EAF1] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-bold text-sm text-[#202938]">{sess.subject_title || "Academic Session"}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-[#728096]">
                        {sess.subject_code}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          sess.status === "OPEN"
                            ? "bg-green-100 text-green-800 animate-pulse"
                            : sess.status === "DRAFT"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {sess.status}
                      </span>
                    </div>

                    <p className="text-xs text-[#728096]">
                      Room: <span className="font-medium text-[#202938]">{sess.classroom_name}</span> &bull; Window: {sess.checkin_window_minutes} mins &bull; QR Interval: {sess.qr_refresh_seconds}s
                    </p>

                    <div className="flex items-center space-x-4 text-xs pt-1">
                      <span className="text-green-700 font-semibold">{sess.total_present} Verified Present</span>
                      <span className="text-amber-700 font-semibold">{sess.total_pending_review} In Review</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    {sess.status === "DRAFT" && (
                      <button
                        onClick={() => handleOpenSession(sess.id)}
                        className="bg-green-600 hover:bg-green-700 text-white text-xs font-semibold px-3 py-2 rounded-[8px] flex items-center space-x-1.5"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Open Window</span>
                      </button>
                    )}

                    {sess.status === "OPEN" && (
                      <>
                        <button
                          onClick={() => setActiveSession(sess)}
                          className="bg-[#2864E8] hover:bg-[#1F55C7] text-white text-xs font-semibold px-3.5 py-2 rounded-[8px] flex items-center space-x-1.5"
                        >
                          <QrCode className="w-3.5 h-3.5" />
                          <span>Display Live QR</span>
                        </button>
                        <button
                          onClick={() => handleCloseSession(sess.id)}
                          className="bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-3 py-2 rounded-[8px] flex items-center space-x-1.5"
                        >
                          <Square className="w-3.5 h-3.5 fill-current" />
                          <span>Close Window</span>
                        </button>
                      </>
                    )}

                    <button
                      onClick={() => openCorrectionModalForSession(sess.id)}
                      className="border border-[#E5EAF1] hover:bg-[#F7F9FC] text-xs font-semibold px-3 py-2 rounded-[8px] text-[#202938] flex items-center space-x-1.5"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-[#728096]" />
                      <span>Correction</span>
                    </button>

                    <a
                      href={`/api/v1/reports/session/${sess.id}/export-csv`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="border border-[#E5EAF1] hover:bg-[#F7F9FC] text-xs font-semibold px-3 py-2 rounded-[8px] text-[#202938] flex items-center space-x-1.5"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5 text-green-600" />
                      <span>CSV Export</span>
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* REVIEW QUEUE TAB */}
      {activeTab === "review" && (
        <div className="bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm">
          <h3 className="text-base font-bold text-[#202938] mb-1">Uncertain Check-In Triage Queue</h3>
          <p className="text-xs text-[#728096] mb-4">
            Submissions flagged by the Explainable Risk Engine due to physical device variations (indoor GPS drift, low light camera, etc.).
          </p>

          {reviewQueue.length === 0 ? (
            <div className="p-8 text-center text-xs text-[#728096]">
              All check-ins cleanly verified. No submissions currently awaiting manual review.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E5EAF1] text-[#728096] uppercase text-[10px]">
                    <th className="pb-2">Student</th>
                    <th className="pb-2">Subject</th>
                    <th className="pb-2">Trigger Reason</th>
                    <th className="pb-2">GPS Evidence</th>
                    <th className="pb-2">Face Evidence</th>
                    <th className="pb-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5EAF1]">
                  {reviewQueue.map((item) => (
                    <tr key={item.attempt_id} className="hover:bg-[#F7F9FC]">
                      <td className="py-3 font-semibold text-[#202938]">
                        <div>{item.student_name}</div>
                        <div className="text-[11px] text-[#728096] font-mono">Roll: {item.roll_number}</div>
                      </td>
                      <td className="py-3 text-[#202938]">{item.subject_title}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                          {item.primary_reason}
                        </span>
                      </td>
                      <td className="py-3 text-[11px] text-[#728096]">
                        <div>Status: {item.geo_status}</div>
                        {item.geo_distance_meters !== null && <div>Dist: {item.geo_distance_meters}m</div>}
                      </td>
                      <td className="py-3 text-[11px] text-[#728096]">
                        <div>Status: {item.face_status}</div>
                        {item.face_similarity_score !== null && <div>Sim: {item.face_similarity_score}</div>}
                      </td>
                      <td className="py-3">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setReviewModalItem(item);
                              setReviewAction("APPROVE");
                              setReviewReason("Verified classroom presence in person");
                            }}
                            className="bg-green-600 hover:bg-green-700 text-white text-[10px] font-bold px-2.5 py-1.5 rounded"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => {
                              setReviewModalItem(item);
                              setReviewAction("REJECT");
                              setReviewReason("Evidence confirmed invalid; student not physically present");
                            }}
                            className="bg-red-600 hover:bg-red-700 text-white text-[10px] font-bold px-2.5 py-1.5 rounded"
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* LIVE DYNAMIC QR STREAM MODAL */}
      {activeSession && liveQRToken && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[16px] max-w-md w-full p-6 text-center space-y-4 shadow-2xl border border-[#E5EAF1]">
            <div className="flex items-center justify-between pb-2 border-b border-[#E5EAF1]">
              <div className="text-left">
                <h3 className="font-bold text-sm text-[#202938]">{activeSession.subject_title}</h3>
                <span className="text-[11px] text-[#728096]">Classroom: {activeSession.classroom_name}</span>
              </div>
              <button
                onClick={() => setActiveSession(null)}
                className="text-[#728096] hover:text-[#202938] text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Countdown Badge */}
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold bg-[#EDF4FF] text-[#2864E8]">
              <Clock className="w-3.5 h-3.5" />
              <span>Token Refreshes in {secondsRemaining}s</span>
            </div>

            {/* Rendered Dynamic QR Code */}
            <div className="p-4 bg-white rounded-xl border-2 border-dashed border-[#2864E8] inline-block shadow-inner">
              <QRCodeSVG value={liveQRToken} size={220} level="M" />
            </div>

            {/* Token Snippet */}
            <div className="p-2 bg-[#F7F9FC] rounded-lg text-[10px] font-mono text-[#728096] truncate">
              HMAC: {liveQRToken.slice(-16)} (Dynamic Cryptographic Signature)
            </div>

            <div className="pt-2 flex justify-between items-center text-xs">
              <span className="text-green-600 font-bold">{activeSession.total_present} Verified Present</span>
              <button
                onClick={() => handleCloseSession(activeSession.id)}
                className="text-red-600 hover:text-red-700 font-semibold"
              >
                Stop Session
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE SESSION MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[16px] max-w-md w-full p-6 space-y-4 shadow-2xl border border-[#E5EAF1]">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-base text-[#202938]">Configure Attendance Session</h3>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-[#728096]">✕</button>
            </div>

            <form onSubmit={handleCreateSession} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Subject</label>
                <select
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="w-full text-xs p-2.5 bg-white border border-[#E5EAF1] rounded-[8px]"
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.code} — {s.title}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Classroom Anchor</label>
                <select
                  value={selectedClassroomId}
                  onChange={(e) => setSelectedClassroomId(e.target.value)}
                  className="w-full text-xs p-2.5 bg-white border border-[#E5EAF1] rounded-[8px]"
                >
                  {classrooms.map((c) => (
                    <option key={c.id} value={c.id}>{c.name} ({c.building})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Window (Mins)</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={checkinWindow}
                    onChange={(e) => setCheckinWindow(Number(e.target.value))}
                    className="w-full text-xs p-2 border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">QR Interval (Secs)</label>
                  <input
                    type="number"
                    min="10"
                    max="120"
                    value={qrRefreshSeconds}
                    onChange={(e) => setQrRefreshSeconds(Number(e.target.value))}
                    className="w-full text-xs p-2 border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
              </div>

              <div className="space-y-2 pt-2 text-xs">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={requireGeo}
                    onChange={(e) => setRequireGeo(e.target.checked)}
                    className="rounded text-[#2864E8]"
                  />
                  <span className="font-semibold text-[#202938]">Enforce Classroom Geofence (Haversine)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={requireFace}
                    onChange={(e) => setRequireFace(e.target.checked)}
                    className="rounded text-[#2864E8]"
                  />
                  <span className="font-semibold text-[#202938]">Enforce Live Face Biometric Verification</span>
                </label>
              </div>

              <button
                type="submit"
                className="w-full mt-4 bg-[#2864E8] hover:bg-[#1F55C7] text-white text-xs font-semibold py-2.5 rounded-[8px] transition-colors"
              >
                Create Session
              </button>
            </form>
          </div>
        </div>
      )}

      {/* REVIEW ACTION MODAL */}
      {reviewModalItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[16px] max-w-md w-full p-6 space-y-4 shadow-2xl border border-[#E5EAF1]">
            <h3 className="font-bold text-base text-[#202938]">
              {reviewAction} Check-In for {reviewModalItem.student_name}
            </h3>
            <p className="text-xs text-[#728096]">
              Trigger: <span className="font-semibold text-[#202938]">{reviewModalItem.primary_reason}</span>
            </p>

            <form onSubmit={handleReviewAction} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">
                  Teacher Justification (Mandatory Audit Requirement)
                </label>
                <textarea
                  required
                  rows={3}
                  value={reviewReason}
                  onChange={(e) => setReviewReason(e.target.value)}
                  placeholder="Explain why this uncertain check-in is being approved or rejected..."
                  className="w-full text-xs p-2 border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              <div className="flex space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReviewModalItem(null)}
                  className="w-1/2 border border-[#E5EAF1] text-xs font-semibold py-2 rounded-[8px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`w-1/2 text-white text-xs font-semibold py-2 rounded-[8px] ${
                    reviewAction === "APPROVE" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"
                  }`}
                >
                  Confirm {reviewAction}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CORRECTION MODAL */}
      {isCorrectionModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[16px] max-w-md w-full p-6 space-y-4 shadow-2xl border border-[#E5EAF1]">
            <h3 className="font-bold text-base text-[#202938]">Apply Manual Attendance Correction</h3>
            <form onSubmit={handleApplyCorrection} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Select Student</label>
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                >
                  {sessionRoster.map((r) => (
                    <option key={r.student_id} value={r.student_id}>
                      {r.student_name} (Roll: {r.roll_number}) — Current: {r.status}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">New Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                >
                  <option value="PRESENT">PRESENT</option>
                  <option value="ABSENT">ABSENT</option>
                  <option value="EXCUSED">EXCUSED (Official Leave / Event)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Mandatory Justification</label>
                <textarea
                  required
                  rows={2}
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  placeholder="e.g. Represented college in Smart India Hackathon zonal round"
                  className="w-full text-xs p-2 border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              <div className="flex space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCorrectionModalOpen(false)}
                  className="w-1/2 border border-[#E5EAF1] text-xs font-semibold py-2 rounded-[8px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 bg-[#2864E8] text-white text-xs font-semibold py-2 rounded-[8px]"
                >
                  Save Correction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

