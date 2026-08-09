interface ConfidenceBadgeProps {
  confidencePct: number;
  verdict?: string;
  className?: string;
}

export function ConfidenceBadge({
  confidencePct,
  verdict = "phishing",
  className = "",
}: ConfidenceBadgeProps) {
  let style = "bg-green-500/15 text-green-400 border-green-500/30";

  if (verdict === "phishing" || confidencePct >= 70) {
    style = "bg-red-500/15 text-red-400 border-red-500/30";
  } else if (verdict === "suspicious" || confidencePct >= 40) {
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
