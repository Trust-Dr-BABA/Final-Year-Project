import { Verdict, VERDICT_COLOR } from "../lib/types";

interface ConfidenceBadgeProps {
  confidencePct: number;
  verdict: Verdict;
  className?: string;
}

// confidence_pct is always >= 50 (ADR-015: it's decisiveness, not risk), so colour is driven by
// verdict alone — the number carries no direction a colour could usefully encode.
export function ConfidenceBadge({ confidencePct, verdict, className = "" }: ConfidenceBadgeProps) {
  return (
    <span
      data-testid="confidence-badge"
      className={`font-data inline-flex items-center px-2 py-0.5 text-[11px] font-medium border ${className}`}
      style={{ color: VERDICT_COLOR[verdict], borderColor: "var(--border)", borderRadius: "var(--radius)" }}
    >
      {confidencePct}% confident
    </span>
  );
}
