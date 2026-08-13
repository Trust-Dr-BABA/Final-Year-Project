import { Verdict } from "../lib/types";

interface VerdictBadgeProps {
  verdict: Verdict;
  className?: string;
}

const STYLES: Record<Verdict, { color: string; bg: string; label: string }> = {
  phishing: { color: "var(--phishing)", bg: "var(--phishing-bg)", label: "Phishing" },
  suspicious: { color: "var(--suspicious)", bg: "var(--suspicious-bg)", label: "Suspicious" },
  legitimate: { color: "var(--safe)", bg: "var(--safe-bg)", label: "Legitimate" },
};

// Verdict pill — sharp corners and a hairline border, not a soft glowing badge.
export function VerdictBadge({ verdict, className = "" }: VerdictBadgeProps) {
  const style = STYLES[verdict];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide border ${className}`}
      style={{ color: style.color, backgroundColor: style.bg, borderColor: style.color, borderRadius: "var(--radius)" }}
    >
      {style.label}
    </span>
  );
}
