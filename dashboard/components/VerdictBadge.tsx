import { Verdict } from "../lib/types";

interface VerdictBadgeProps {
  verdict: Verdict;
  className?: string;
}

export function VerdictBadge({
  verdict,
  className = "",
}: VerdictBadgeProps) {
  let style = "bg-green-500/15 text-green-400 border-green-500/30";
  let label = "Legitimate";

  if (verdict === "phishing") {
    style = "bg-red-500/15 text-red-400 border-red-500/30";
    label = "Phishing";
  } else if (verdict === "suspicious") {
    style = "bg-amber-500/15 text-amber-400 border-amber-500/30";
    label = "Suspicious";
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      {label}
    </span>
  );
}
