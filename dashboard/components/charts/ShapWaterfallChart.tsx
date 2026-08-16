"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ShapReason } from "../../lib/types";
import { useChartColors } from "../../lib/useChartColors";

interface ShapWaterfallChartProps {
  reasons: ShapReason[];
}

// Horizontal bars, one per attribution, red for risk-increasing / green for risk-decreasing.
// Browser-signal attributions (from the fusion layer) and SHAP attributions render identically
// here — both are additive log-odds contributions (ADR-014), so nothing in this chart needs to
// know which family produced a given bar.
export function ShapWaterfallChart({ reasons }: ShapWaterfallChartProps) {
  const { phishing, safe, text, textMuted, border, bgRaised } = useChartColors();

  if (reasons.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        No attributions recorded for this scan.
      </p>
    );
  }

  const data = [...reasons]
    .sort((a, b) => Math.abs(b.shap_impact) - Math.abs(a.shap_impact))
    .slice(0, 5)
    .map((r) => ({
      name: r.human_readable.length > 42 ? r.human_readable.slice(0, 40) + "…" : r.human_readable,
      full: r.human_readable,
      impact: r.shap_impact,
    }))
    .reverse(); // largest at top

  return (
    <ResponsiveContainer width="100%" height={Math.max(140, data.length * 44)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }}>
        <XAxis type="number" tick={{ fill: textMuted, fontSize: 11 }} axisLine={{ stroke: border }} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={220}
          tick={{ fill: text, fontSize: 11 }}
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
            maxWidth: 280,
            whiteSpace: "normal",
            wordBreak: "break-word",
          }}
          labelStyle={{ color: text }}
          itemStyle={{ color: text }}
          formatter={(value) => [typeof value === "number" ? value.toFixed(3) : String(value), "log-odds impact"]}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.full ?? ""}
        />
        <Bar dataKey="impact" radius={2} barSize={18}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.impact >= 0 ? phishing : safe} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
