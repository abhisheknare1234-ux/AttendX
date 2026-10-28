"use client";

import React, { useState, useEffect } from "react";
import { Users, Building, BookOpen, ShieldCheck, Plus, RefreshCw, AlertCircle, CheckCircle, FileText } from "lucide-react";
import { api } from "@/lib/api";

export default function AdminDashboard({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState<"overview" | "users" | "academics" | "audit">("overview");
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // User Provisioning State
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPass, setNewUserPass] = useState("");
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newUserRole, setNewUserRole] = useState("STUDENT");
  const [newRollNo, setNewRollNo] = useState("");
  const [newPrn, setNewPrn] = useState("");
  const [newEmpId, setNewEmpId] = useState("");

  // Classroom Setup State
  const [roomName, setRoomName] = useState("");
  const [roomBuilding, setRoomBuilding] = useState("Building A - ZCOER");
  const [roomLat, setRoomLat] = useState("18.4485");
  const [roomLon, setRoomLon] = useState("73.8245");
  const [roomRadius, setRoomRadius] = useState("100");

  // Class & Subject State
  const [newClassName, setNewClassName] = useState("");
  const [newSubjCode, setNewSubjCode] = useState("");
  const [newSubjTitle, setNewSubjTitle] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, h, u, r, c, sub, a] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.getHealth().catch(() => null),
        api.getUsers().catch(() => []),
        api.getClassrooms().catch(() => []),
        api.getClasses().catch(() => []),
        api.getSubjects().catch(() => []),
        api.getAuditLogs().catch(() => []),
      ]);
      setStats(s);
      setHealth(h);
      setUsersList(u);
      setClassrooms(r);
      setClasses(c);
      setSubjects(sub);
      setAuditLogs(a);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await api.provisionUser({
        email: newUserEmail,
        password: newUserPass,
        first_name: newFirstName,
        last_name: newLastName,
        role: newUserRole,
        roll_number: newUserRole === "STUDENT" ? newRollNo : undefined,
        prn: newUserRole === "STUDENT" ? newPrn : undefined,
        employee_id: newUserRole === "TEACHER" ? newEmpId : undefined,
      });
      setMessage({ text: "User successfully provisioned with institutional profile.", type: "success" });
      setNewUserEmail("");
      setNewUserPass("");
      setNewFirstName("");
      setNewLastName("");
      setNewRollNo("");
      setNewPrn("");
      setNewEmpId("");
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to provision user.", type: "error" });
    }
  };

  const handleCreateClassroom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createClassroom({
        name: roomName,
        building: roomBuilding,
        latitude: parseFloat(roomLat),
        longitude: parseFloat(roomLon),
        radius_meters: parseFloat(roomRadius),
      });
      setMessage({ text: "Classroom and geofence boundary registered.", type: "success" });
      setRoomName("");
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createClass({ name: newClassName, academic_year: "2026-2027", semester: 6 });
      setMessage({ text: "Academic class registered.", type: "success" });
      setNewClassName("");
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId) {
      setMessage({ text: "Select a class first.", type: "error" });
      return;
    }
    try {
      await api.createSubject({ code: newSubjCode, title: newSubjTitle, class_id: selectedClassId });
      setMessage({ text: "Academic subject created.", type: "success" });
      setNewSubjCode("");
      setNewSubjTitle("");
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Welcome Card */}
      <div className="bg-white rounded-[14px] border border-[#E5EAF1] p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-[#202938]">Institutional Administration Console</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-[#2864E8]">
              ZEAL College Node
            </span>
          </div>
          <p className="text-xs text-[#728096] mt-1">
            Logged in as {user.first_name} {user.last_name} ({user.email}) &bull; Role: {user.role}
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-[#2864E8] bg-[#EDF4FF] hover:bg-blue-100 px-3.5 py-2 rounded-[9px] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Database</span>
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded-[12px] text-xs font-medium flex items-center space-x-2 border ${
            message.type === "success"
              ? "bg-green-50 text-green-800 border-green-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {message.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[#E5EAF1] space-x-6 text-sm">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "overview"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>System Health & Metrics</span>
        </button>
        <button
          onClick={() => setActiveTab("users")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "users"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>User Accounts ({usersList.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("academics")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "academics"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <Building className="w-4 h-4" />
          <span>Academic & Geofences</span>
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-3 font-semibold transition-colors flex items-center space-x-2 ${
            activeTab === "audit"
              ? "border-b-2 border-[#2864E8] text-[#2864E8]"
              : "text-[#728096] hover:text-[#202938]"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Security Audit Trail</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW & SYSTEM HEALTH */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-[14px] border border-[#E5EAF1] shadow-sm">
              <span className="text-xs font-semibold text-[#728096] uppercase tracking-wider block">Authorized Users</span>
              <span className="text-2xl font-bold text-[#202938] mt-1 block">{stats?.total_users ?? "--"}</span>
              <span className="text-[11px] text-[#728096] mt-1 block">
                {stats?.total_teachers ?? 0} Faculty &bull; {stats?.total_students ?? 0} Students
              </span>
            </div>

            <div className="bg-white p-5 rounded-[14px] border border-[#E5EAF1] shadow-sm">
              <span className="text-xs font-semibold text-[#728096] uppercase tracking-wider block">Active Sessions</span>
              <span className="text-2xl font-bold text-[#2864E8] mt-1 block">{stats?.active_sessions ?? "--"}</span>
              <span className="text-[11px] text-[#728096] mt-1 block">
                Total completed: {stats?.total_sessions ?? 0}
              </span>
            </div>

            <div className="bg-white p-5 rounded-[14px] border border-[#E5EAF1] shadow-sm">
              <span className="text-xs font-semibold text-[#728096] uppercase tracking-wider block">Avg Campus Attendance</span>
              <span className="text-2xl font-bold text-green-600 mt-1 block">{stats?.average_attendance_percentage ?? 0}%</span>
              <span className="text-[11px] text-[#728096] mt-1 block">
                {stats?.total_present ?? 0} present ledger records
              </span>
            </div>

            <div className="bg-white p-5 rounded-[14px] border border-[#E5EAF1] shadow-sm">
              <span className="text-xs font-semibold text-[#728096] uppercase tracking-wider block">Review Queue</span>
              <span className="text-2xl font-bold text-amber-600 mt-1 block">{stats?.total_pending_review ?? 0}</span>
              <span className="text-[11px] text-[#728096] mt-1 block">Awaiting teacher verification</span>
            </div>
          </div>

          {/* Subsystems Health Card */}
          <div className="bg-white rounded-[14px] border border-[#E5EAF1] p-6 shadow-sm">
            <h3 className="text-base font-bold text-[#202938] mb-4">Verification Engine Subsystems Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-[#E5EAF1] bg-[#F7F9FC]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#202938]">Database Connection</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-800">
                    {health?.services?.database?.status || "CONNECTED"}
                  </span>
                </div>
                <p className="text-xs text-[#728096]">
                  Engine: {health?.services?.database?.engine || "PostgreSQL/SQLite"} &bull; UTC Synchronized
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#E5EAF1] bg-[#F7F9FC]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#202938]">QR Crypto Validator</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-800">
                    {health?.services?.qr_crypto_validator?.status || "OPERATIONAL"}
                  </span>
                </div>
                <p className="text-xs text-[#728096]">
                  HMAC-SHA256 &bull; {health?.services?.qr_crypto_validator?.refresh_interval_seconds || 30}s Dynamic Rotation
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#E5EAF1] bg-[#F7F9FC]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#202938]">Classroom Geofence Engine</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-800">
                    {health?.services?.geofence_engine?.status || "OPERATIONAL"}
                  </span>
                </div>
                <p className="text-xs text-[#728096]">
                  WGS-84 Haversine Spherical Anchor: ZEAL College Narhe (18.4485°N, 73.8245°E)
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#E5EAF1] bg-[#F7F9FC]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#202938]">Biometric Face Engine</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-800">
                    {health?.services?.biometric_verifier?.status || "OPERATIONAL"}
                  </span>
                </div>
                <p className="text-xs text-[#728096]">
                  Cosine Similarity Threshold: {health?.services?.biometric_verifier?.threshold || 0.75}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: USER PROVISIONING */}
      {activeTab === "users" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Create User Form */}
          <div className="bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm">
            <h3 className="text-base font-bold text-[#202938] mb-1">Provision Institutional Account</h3>
            <p className="text-xs text-[#728096] mb-4">
              Add authorized faculty or students with strict role permissions.
            </p>

            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="w-full text-xs p-2.5 bg-white border border-[#E5EAF1] rounded-[8px]"
                >
                  <option value="STUDENT">Student</option>
                  <option value="TEACHER">Faculty / Teacher</option>
                  <option value="ADMIN">Administrator</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    value={newFirstName}
                    onChange={(e) => setNewFirstName(e.target.value)}
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Last Name</label>
                  <input
                    type="text"
                    required
                    value={newLastName}
                    onChange={(e) => setNewLastName(e.target.value)}
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Institutional Email</label>
                <input
                  type="email"
                  required
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="user@zeal.edu.in"
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={newUserPass}
                  onChange={(e) => setNewUserPass(e.target.value)}
                  placeholder="Min 8 characters"
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              {newUserRole === "STUDENT" && (
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <label className="block text-xs font-semibold text-[#202938] mb-1">Roll Number</label>
                    <input
                      type="text"
                      required
                      value={newRollNo}
                      onChange={(e) => setNewRollNo(e.target.value)}
                      placeholder="e.g. AIDS-042"
                      className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#202938] mb-1">PRN</label>
                    <input
                      type="text"
                      required
                      value={newPrn}
                      onChange={(e) => setNewPrn(e.target.value)}
                      placeholder="e.g. 71920042"
                      className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                    />
                  </div>
                </div>
              )}

              {newUserRole === "TEACHER" && (
                <div className="pt-1">
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Employee ID</label>
                  <input
                    type="text"
                    required
                    value={newEmpId}
                    onChange={(e) => setNewEmpId(e.target.value)}
                    placeholder="e.g. EMP-AIDS-10"
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
              )}

              <button
                type="submit"
                className="w-full mt-3 bg-[#2864E8] hover:bg-[#1F55C7] text-white text-xs font-semibold py-2.5 rounded-[8px] transition-colors"
              >
                Provision User
              </button>
            </form>
          </div>

          {/* User Roster Table */}
          <div className="lg:col-span-2 bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm">
            <h3 className="text-base font-bold text-[#202938] mb-4">Provisioned Accounts ({usersList.length})</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E5EAF1] text-[#728096] uppercase text-[10px]">
                    <th className="pb-2">User</th>
                    <th className="pb-2">Role</th>
                    <th className="pb-2">Identifiers</th>
                    <th className="pb-2">Biometrics</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5EAF1]">
                  {usersList.map((u) => (
                    <tr key={u.id} className="hover:bg-[#F7F9FC]">
                      <td className="py-2.5 font-medium text-[#202938]">
                        <div>{u.first_name} {u.last_name}</div>
                        <div className="text-[11px] text-[#728096]">{u.email}</div>
                      </td>
                      <td className="py-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          u.role === "ADMIN" ? "bg-purple-100 text-purple-800" :
                          u.role === "TEACHER" ? "bg-blue-100 text-blue-800" : "bg-emerald-100 text-emerald-800"
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-2.5 text-[#728096]">
                        {u.roll_number && <span>Roll: {u.roll_number} </span>}
                        {u.employee_id && <span>Emp: {u.employee_id} </span>}
                      </td>
                      <td className="py-2.5">
                        {u.role === "STUDENT" ? (
                          u.is_biometric_enrolled ? (
                            <span className="text-[10px] text-green-700 font-semibold bg-green-50 px-2 py-0.5 rounded">Enrolled</span>
                          ) : (
                            <span className="text-[10px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded">Pending</span>
                          )
                        ) : (
                          <span className="text-[10px] text-[#728096]">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: ACADEMIC & GEOFENCES */}
      {activeTab === "academics" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Classrooms & Geofences */}
          <div className="bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm space-y-4">
            <h3 className="text-base font-bold text-[#202938]">Register Physical Classroom Geofence</h3>
            <form onSubmit={handleCreateClassroom} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Classroom Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Lab 304 - High Performance AI Lab"
                  value={roomName}
                  onChange={(e) => setRoomName(e.target.value)}
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#202938] mb-1">Building</label>
                <input
                  type="text"
                  required
                  value={roomBuilding}
                  onChange={(e) => setRoomBuilding(e.target.value)}
                  className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={roomLat}
                    onChange={(e) => setRoomLat(e.target.value)}
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={roomLon}
                    onChange={(e) => setRoomLon(e.target.value)}
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#202938] mb-1">Radius (m)</label>
                  <input
                    type="number"
                    required
                    value={roomRadius}
                    onChange={(e) => setRoomRadius(e.target.value)}
                    className="w-full text-xs p-2 bg-white border border-[#E5EAF1] rounded-[8px]"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-[#2864E8] text-white text-xs font-semibold py-2.5 rounded-[8px] hover:bg-[#1F55C7] transition-colors"
              >
                Register Classroom Anchor
              </button>
            </form>

            <div className="pt-4 border-t border-[#E5EAF1]">
              <h4 className="text-xs font-bold text-[#728096] uppercase mb-2">Registered Classrooms</h4>
              <div className="space-y-2">
                {classrooms.map((c) => (
                  <div key={c.id} className="p-2.5 rounded-lg border border-[#E5EAF1] text-xs flex justify-between items-center">
                    <div>
                      <span className="font-semibold text-[#202938] block">{c.name}</span>
                      <span className="text-[#728096] text-[11px]">{c.building} &bull; Radius: {c.radius_meters}m</span>
                    </div>
                    <span className="text-[10px] text-[#2864E8] font-mono">
                      {c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Classes & Subjects */}
          <div className="bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm space-y-4">
            <h3 className="text-base font-bold text-[#202938]">Classes & Academic Subjects</h3>
            <div className="grid grid-cols-2 gap-3">
              <form onSubmit={handleCreateClass} className="p-3 border border-[#E5EAF1] rounded-lg space-y-2">
                <span className="text-xs font-bold text-[#202938] block">Add Class</span>
                <input
                  type="text"
                  required
                  placeholder="e.g. TE-AIDS-DivA"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                  className="w-full text-xs p-1.5 border border-[#E5EAF1] rounded"
                />
                <button type="submit" className="w-full text-xs bg-[#2864E8] text-white py-1.5 rounded font-semibold">
                  Create Class
                </button>
              </form>

              <form onSubmit={handleCreateSubject} className="p-3 border border-[#E5EAF1] rounded-lg space-y-2">
                <span className="text-xs font-bold text-[#202938] block">Add Subject</span>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  className="w-full text-xs p-1 border border-[#E5EAF1] rounded"
                >
                  <option value="">Select Class</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>{cls.name}</option>
                  ))}
                </select>
                <input
                  type="text"
                  required
                  placeholder="Code (e.g. AIDS-401)"
                  value={newSubjCode}
                  onChange={(e) => setNewSubjCode(e.target.value)}
                  className="w-full text-xs p-1.5 border border-[#E5EAF1] rounded"
                />
                <input
                  type="text"
                  required
                  placeholder="Title"
                  value={newSubjTitle}
                  onChange={(e) => setNewSubjTitle(e.target.value)}
                  className="w-full text-xs p-1.5 border border-[#E5EAF1] rounded"
                />
                <button type="submit" className="w-full text-xs bg-[#2864E8] text-white py-1.5 rounded font-semibold">
                  Create Subject
                </button>
              </form>
            </div>

            <div className="pt-2">
              <h4 className="text-xs font-bold text-[#728096] uppercase mb-2">Subject Catalog</h4>
              <div className="space-y-2">
                {subjects.map((s) => (
                  <div key={s.id} className="p-2.5 rounded-lg border border-[#E5EAF1] text-xs flex justify-between items-center">
                    <div>
                      <span className="font-semibold text-[#202938] block">{s.code} — {s.title}</span>
                      <span className="text-[#728096] text-[11px]">Class: {s.class_name || "N/A"}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT TRAIL */}
      {activeTab === "audit" && (
        <div className="bg-white p-6 rounded-[14px] border border-[#E5EAF1] shadow-sm">
          <h3 className="text-base font-bold text-[#202938] mb-1">Immutable Security & Administrative Ledger</h3>
          <p className="text-xs text-[#728096] mb-4">
            Auditing sensitive events: authentication successes/failures, session lifecycles, and manual overrides.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E5EAF1] text-[#728096] uppercase text-[10px]">
                  <th className="pb-2">Timestamp UTC</th>
                  <th className="pb-2">Action</th>
                  <th className="pb-2">Target</th>
                  <th className="pb-2">Details</th>
                  <th className="pb-2">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5EAF1] font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#F7F9FC]">
                    <td className="py-2.5 text-[#728096] whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="py-2.5">
                      <span className="font-bold text-[#2864E8]">{log.action}</span>
                    </td>
                    <td className="py-2.5 text-[#202938]">
                      {log.target_type}:{log.target_id?.slice(0, 8)}
                    </td>
                    <td className="py-2.5 text-[#728096] max-w-xs truncate">{log.details || "—"}</td>
                    <td className="py-2.5 text-[#728096]">{log.ip_address || "127.0.0.1"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
