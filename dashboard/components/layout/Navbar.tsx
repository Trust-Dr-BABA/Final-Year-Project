import Link from "next/link";
import { ThemeToggle } from "../ThemeToggle";

// Sticky top navigation: wordmark, section links, theme toggle, API docs link.
export function Navbar() {
  return (
    <header
      className="sticky top-0 z-50 border-b"
      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg)" }}
    >
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-baseline gap-2">
          <span
            className="font-semibold text-[15px] tracking-tight"
            style={{ color: "var(--text)" }}
          >
            Explainable Security Analyst
          </span>
        </Link>

        <nav
          className="flex items-center gap-6 text-[13px]"
          style={{ color: "var(--text-muted)" }}
        >
          <Link
            href="/"
            className="hover:opacity-70 transition-opacity"
            style={{ color: "var(--text)" }}
          >
            Overview
          </Link>
          <Link
            href="/history"
            className="hover:opacity-70 transition-opacity"
            style={{ color: "var(--text)" }}
          >
            History
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
