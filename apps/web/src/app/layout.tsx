import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AttendX AI — Smart Attendance & Anti-Proxy System",
  description: "Institutional-Grade Verification & Anti-Proxy Attendance Platform for ZEAL College of Engineering & Research, Pune",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-[#F7F9FC] text-[#202938]">
        {children}
      </body>
    </html>
  );
}
