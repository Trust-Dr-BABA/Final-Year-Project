import { Verdict, VERDICT_COLOR } from "../lib/types";

interface VerdictBadgeProps {
  verdict: Verdict;
  className?: string;
}

const BG: Record<Verdict, string> = {
  phishing: "var(--phishing-bg)",
  suspicious: "var(--suspicious-bg)",
  legitimate: "var(--safe-bg)",
};

const LABEL: Record<Verdict, string> = {
  phishing: "Phishing",
  suspicious: "Suspicious",
  legitimate: "Legitimate",
};

// Verdict pill — sharp corners and a hairline border, not a soft glowing badge.
export function VerdictBadge({ verdict, className = "" }: VerdictBadgeProps) {
  const color = VERDICT_COLOR[verdict];
  return (
    <span
      data-testid="verdict-badge"
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide border ${className}`}
      style={{ color, backgroundColor: BG[verdict], borderColor: color, borderRadius: "var(--radius)" }}
    >
      {LABEL[verdict]}
    </span>
  );
}
