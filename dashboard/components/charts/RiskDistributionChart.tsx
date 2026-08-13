"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useCssVar } from "../../lib/useCssVar";

interface RiskDistributionChartProps {
  phishingCount: number;
  suspiciousCount: number;
  legitimateCount: number;
}

// Horizontal bar chart of verdict counts — a real chart, not a placeholder div.
export function RiskDistributionChart({
  phishingCount,
  suspiciousCount,
  legitimateCount,
}: RiskDistributionChartProps) {
  const safe = useCssVar("--safe", "#15803d");
  const suspicious = useCssVar("--suspicious", "#a3540c");
  const phishing = useCssVar("--phishing", "#b91c1c");
  const text = useCssVar("--text", "#1a1917");
  const textMuted = useCssVar("--text-muted", "#6b6860");
  const border = useCssVar("--border", "#ddd9d0");
  const bgRaised = useCssVar("--bg-raised", "#ffffff");

  const data = [
    { name: "Legitimate", count: legitimateCount, color: safe },
    { name: "Suspicious", count: suspiciousCount, color: suspicious },
    { name: "Phishing", count: phishingCount, color: phishing },
  ];

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
        <XAxis type="number" allowDecimals={false} tick={{ fill: textMuted, fontSize: 11 }} axisLine={{ stroke: border }} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={80}
          tick={{ fill: text, fontSize: 12 }}
          axisLine={{ stroke: border }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: border, opacity: 0.3 }}
          contentStyle={{ background: bgRaised, border: `1px solid ${border}`, borderRadius: 3, fontSize: 12 }}
          labelStyle={{ color: text }}
        />
        <Bar dataKey="count" radius={[0, 2, 2, 0]} barSize={22}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
