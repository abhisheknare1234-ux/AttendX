"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import AdminDashboard from "@/components/AdminDashboard";
import TeacherDashboard from "@/components/TeacherDashboard";
import StudentDashboard from "@/components/StudentDashboard";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const u = await api.getMe();
        setUser(u);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchMe();
  }, []);

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-7 h-7 border-2 border-[#2864E8] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (user.role === "ADMIN") {
    return <AdminDashboard user={user} />;
  }

  if (user.role === "TEACHER") {
    return <TeacherDashboard user={user} />;
  }

  return <StudentDashboard user={user} />;
}
