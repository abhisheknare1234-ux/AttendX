"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield, Users, Clock, LogOut, BookOpen, Layers, Menu, X } from "lucide-react";
import { api } from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const u = await api.getMe();
        setUser(u);
      } catch (err) {
        router.push("/");
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [router]);

  const handleLogout = async () => {
    await api.logout();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F7F9FC]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-3 border-[#2864E8] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-semibold text-[#728096]">Loading AttendX AI Workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#F7F9FC]">
      {/* SIDEBAR (Desktop) */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-[#E5EAF1] flex-col justify-between p-5 shrink-0">
        <div className="space-y-6">
          {/* Logo & Institution */}
          <div className="flex items-center space-x-3 px-2">
            <div className="bg-[#2864E8] p-2 rounded-xl text-white shadow-sm">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-[#202938]">AttendX AI</span>
              <span className="block text-[10px] font-semibold text-[#728096] uppercase tracking-wider">
                Anti-Proxy Engine
              </span>
            </div>
          </div>

          <div className="px-2">
            <div className="text-[11px] font-semibold text-[#2864E8] bg-[#EDF4FF] px-3 py-1.5 rounded-lg border border-blue-100">
              ZEAL College Node (ZCOER)
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <div className="flex items-center space-x-3 px-3 py-2.5 rounded-[9px] bg-[#EDF4FF] text-[#2864E8] font-bold text-xs">
              <Layers className="w-4 h-4 text-[#2864E8]" />
              <span>Workspace Dashboard</span>
            </div>
          </nav>
        </div>

        {/* User Card & Logout */}
        <div className="pt-4 border-t border-[#E5EAF1] space-y-3">
          <div className="px-2">
            <span className="text-xs font-bold text-[#202938] block truncate">
              {user?.first_name} {user?.last_name}
            </span>
            <span className="text-[11px] text-[#728096] block truncate">{user?.email}</span>
            <span className="inline-block mt-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-[#2864E8]">
              {user?.role}
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-2 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 p-2 rounded-[8px] transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="bg-white border-b border-[#E5EAF1] h-16 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-[#728096] hover:text-[#202938]"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <span className="text-xs font-semibold text-[#728096] hidden sm:inline">
              Institutional Context: <span className="text-[#202938] font-bold">ZEAL College of Engineering & Research, Pune</span>
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-bold text-[#202938]">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="text-[10px] font-semibold text-[#728096] uppercase">{user?.role}</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-[#EDF4FF] text-[#2864E8] font-bold text-xs flex items-center justify-center border border-blue-200">
              {user?.first_name?.[0] || "U"}
            </div>
          </div>
        </header>

        {/* Workspace Body */}
        <main className="flex-1 p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

