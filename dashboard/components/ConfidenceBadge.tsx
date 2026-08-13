import { Verdict } from "../lib/types";

interface ConfidenceBadgeProps {
  confidencePct: number;
  verdict: Verdict;
  className?: string;
}

// Colored pill showing confidence_pct. Color is driven by verdict alone — confidence_pct is
// always >= 50 (ADR-015: it's decisiveness, not risk), so it carries no directional information
// a color could usefully encode.
export function ConfidenceBadge({
  confidencePct,
  verdict,
  className = "",
}: ConfidenceBadgeProps) {
  let style = "bg-green-500/15 text-green-400 border-green-500/30";

  if (verdict === "phishing") {
    style = "bg-red-500/15 text-red-400 border-red-500/30";
  } else if (verdict === "suspicious") {
    style = "bg-amber-500/15 text-amber-400 border-amber-500/30";
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      {confidencePct}% confident
    </span>
  );
}
