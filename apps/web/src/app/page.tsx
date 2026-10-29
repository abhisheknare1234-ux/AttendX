"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, QrCode, MapPin, ScanFace, Lock, AlertCircle, ArrowRight, Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@zeal.attendx.ai");
  const [password, setPassword] = useState("ZealAdmin@2026Secure!");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to authenticate. Please check institutional credentials.");
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#F7F9FC]">
      {/* LEFT PANEL - Royal Blue Brand Identity */}
      <div className="lg:w-1/2 bg-[#2864E8] text-white p-8 lg:p-14 flex flex-col justify-between relative overflow-hidden">
        {/* Subtle geometric background overlay */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white via-transparent to-transparent pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-6">
            <div className="bg-white/15 p-2.5 rounded-xl border border-white/20 backdrop-blur-sm">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <span className="text-2xl font-bold tracking-tight">AttendX AI</span>
              <span className="block text-xs font-medium text-blue-100 tracking-wide uppercase">Anti-Proxy Intelligence</span>
            </div>
          </div>
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-blue-100 border border-white/15 mb-6">
            ZEAL College of Engineering & Research, Pune
          </div>
        </div>

        {/* Center Presentation Graphic & Content */}
        <div className="relative z-10 my-8 lg:my-0 space-y-6 max-w-lg">
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight leading-tight">
            Institutional-Grade Attendance Verification & Anti-Proxy Security
          </h1>
          <p className="text-blue-100 text-sm lg:text-base leading-relaxed">
            Eliminating proxy attendance through an explainable multi-factor verification engine: dynamic signed QR tokens, spatial GPS geofencing, live facial biometrics, and verifiable audit trails.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-4">
            <div className="flex items-start space-x-3 bg-white/10 p-3 rounded-xl border border-white/15">
              <QrCode className="w-5 h-5 text-blue-200 mt-0.5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-white">Dynamic Cryptographic QR</h4>
                <p className="text-[11px] text-blue-100">30s HMAC-SHA256 tokens resist photo sharing</p>
              </div>
            </div>

            <div className="flex items-start space-x-3 bg-white/10 p-3 rounded-xl border border-white/15">
              <MapPin className="w-5 h-5 text-blue-200 mt-0.5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-white">Classroom Geofencing</h4>
                <p className="text-[11px] text-blue-100">Haversine spherical distance & accuracy check</p>
              </div>
            </div>

            <div className="flex items-start space-x-3 bg-white/10 p-3 rounded-xl border border-white/15">
              <ScanFace className="w-5 h-5 text-blue-200 mt-0.5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-white">Biometric Verification</h4>
                <p className="text-[11px] text-blue-100">Cosine similarity vs registered reference</p>
              </div>
            </div>

            <div className="flex items-start space-x-3 bg-white/10 p-3 rounded-xl border border-white/15">
              <Shield className="w-5 h-5 text-blue-200 mt-0.5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-white">Explainable Risk Engine</h4>
                <p className="text-[11px] text-blue-100">Transparent reason codes & teacher review queue</p>
              </div>
            </div>
          </div>
        </div>

        {/* Left Footer */}
        <div className="relative z-10 pt-4 border-t border-white/15 text-xs text-blue-100 flex items-center justify-between">
          <span>Target Context: Dept of AI & Data Science (ZCOER)</span>
          <span className="font-mono">v1.0.0</span>
        </div>
      </div>

      {/* RIGHT PANEL - Clean Modern Login Experience */}
      <div className="lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="bg-white rounded-[14px] border border-[#E5EAF1] p-8 shadow-sm">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-[#202938]">Institutional Sign In</h2>
              <p className="text-sm text-[#728096] mt-1">
                Enter your authorized college credentials to access the verification workspace.
              </p>
            </div>

            {error && (
              <div className="mb-5 p-3.5 rounded-lg bg-red-50 border border-red-200 flex items-start space-x-2.5 text-red-700 text-sm">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#202938] uppercase tracking-wider mb-1.5">
                  Institutional Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. name@zeal.edu.in"
                  className="w-full px-3.5 py-2.5 text-sm bg-white border border-[#E5EAF1] rounded-[9px] text-[#202938] placeholder-[#728096] focus:outline-none focus:ring-2 focus:ring-[#2864E8] focus:border-transparent transition-all"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-[#202938] uppercase tracking-wider">
                    Password
                  </label>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter account password"
                    className="w-full px-3.5 py-2.5 text-sm bg-white border border-[#E5EAF1] rounded-[9px] text-[#202938] placeholder-[#728096] focus:outline-none focus:ring-2 focus:ring-[#2864E8] focus:border-transparent transition-all pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#728096] hover:text-[#202938]"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 bg-[#2864E8] hover:bg-[#1F55C7] text-white font-medium py-2.5 px-4 rounded-[9px] flex items-center justify-center space-x-2 transition-colors disabled:opacity-60 shadow-sm"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Authenticate with AttendX</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* DEMO PROFILE SELECTOR FOR FACULTY EVALUATION */}
            <div className="mt-8 pt-6 border-t border-[#E5EAF1]">
              <p className="text-xs font-semibold text-[#728096] uppercase tracking-wider mb-2.5 text-center">
                Quick-Load Evaluation Accounts
              </p>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => setDemoCredentials("admin@zeal.attendx.ai", "ZealAdmin@2026Secure!")}
                  className="w-full text-left p-2.5 rounded-lg border border-[#E5EAF1] hover:border-[#2864E8] hover:bg-[#EDF4FF] transition-all flex items-center justify-between text-xs group"
                >
                  <div>
                    <span className="font-bold text-[#202938] block group-hover:text-[#2864E8]">Administrator</span>
                    <span className="text-[#728096] text-[11px]">admin@zeal.attendx.ai (Full institutional access)</span>
                  </div>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-100 text-[#2864E8]">Bootstrap</span>
                </button>
              </div>
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="mt-4 text-center text-xs text-[#728096] space-y-1">
            <p>Protected by AttendX AI Cryptographic Proof of Presence.</p>
            <p>Biometric and location data processed according to institutional privacy policy.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

