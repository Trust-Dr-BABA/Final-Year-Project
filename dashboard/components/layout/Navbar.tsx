import Link from "next/link";
import React from "react";

export const Navbar: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-[#0f0f1a]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 text-slate-100 font-bold text-lg">
          <span className="text-xl">🛡️</span>
          <span>Explainable Security Analyst</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-normal">
            v0.1.0
          </span>
        </Link>

        <nav className="flex items-center space-x-6 text-sm font-medium text-slate-300">
          <Link
            href="/"
            className="hover:text-white transition-colors duration-150"
          >
            Overview
          </Link>
          <Link
            href="/history"
            className="hover:text-white transition-colors duration-150"
          >
            Scan History
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors duration-150 text-slate-400"
          >
            API Docs ↗
          </a>
        </nav>
      </div>
    </header>
  );
};
