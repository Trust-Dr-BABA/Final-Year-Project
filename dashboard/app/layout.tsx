import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "../components/layout/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Explainable Security Analyst — Dashboard",
  description:
    "AI-Powered Phishing & Privacy Risk Detection with SHAP Plain-English Explanations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-[#0f0f1a] text-slate-100 min-h-screen antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
