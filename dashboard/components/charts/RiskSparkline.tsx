"use client";

import { format } from "date-fns";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Scan } from "../../lib/types";
import { useCssVar } from "../../lib/useCssVar";

interface RiskSparklineProps {
  scans: Scan[];
}

// Risk over time across repeat scans of the same URL, oldest first.
export function RiskSparkline({ scans }: RiskSparklineProps) {
  const accent = useCssVar("--accent", "#0d7d72");
  const textMuted = useCssVar("--text-muted", "#6b6860");
  const border = useCssVar("--border", "#ddd9d0");
  const bgRaised = useCssVar("--bg-raised", "#ffffff");
  const text = useCssVar("--text", "#1a1917");

  if (scans.length < 2) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        Only one recorded scan for this URL — no trend to show yet.
      </p>
    );
  }

  const data = [...scans]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((s) => ({
      date: format(new Date(s.created_at), "MMM d, HH:mm"),
      risk: Math.round(s.risk_score * 100),
    }));

  return (
    <ResponsiveContainer width="100%" height={140}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -16 }}>
        <XAxis dataKey="date" tick={{ fill: textMuted, fontSize: 10 }} axisLine={{ stroke: border }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: textMuted, fontSize: 10 }} axisLine={{ stroke: border }} tickLine={false} />
        <Tooltip
          contentStyle={{ background: bgRaised, border: `1px solid ${border}`, borderRadius: 3, fontSize: 12 }}
          labelStyle={{ color: text }}
          formatter={(value) => [`${value}%`, "risk"]}
        />
        <Line type="monotone" dataKey="risk" stroke={accent} strokeWidth={2} dot={{ r: 3, fill: accent }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
