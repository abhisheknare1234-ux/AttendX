import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

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
    <html lang="en" className={inter.className}>
      <body className="min-h-screen bg-[#F7F9FC] text-[#202938]">
        {children}
      </body>
    </html>
  );
}

