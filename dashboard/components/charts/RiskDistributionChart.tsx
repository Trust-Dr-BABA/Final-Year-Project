"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useChartColors } from "../../lib/useChartColors";

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
  const { safe, suspicious, phishing, text, textMuted, border, bgRaised } = useChartColors();

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
          contentStyle={{
            background: bgRaised,
            border: `1px solid ${border}`,
            borderRadius: 3,
            fontSize: 12,
            maxWidth: 200,
            whiteSpace: "normal",
            wordBreak: "break-word",
          }}
          labelStyle={{ color: text }}
          itemStyle={{ color: text }}
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
