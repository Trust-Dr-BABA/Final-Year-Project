"use client";

import { useCssVar } from "./useCssVar";

export interface ChartColors {
  phishing: string;
  suspicious: string;
  safe: string;
  text: string;
  textMuted: string;
  border: string;
  bgRaised: string;
}

// The set of theme colours recharts needs resolved to literal values (see useCssVar) — shared by
// every chart component so each doesn't repeat the same seven useCssVar calls with the same
// fallbacks. A component that doesn't need every colour just doesn't destructure it.
export function useChartColors(): ChartColors {
  return {
    phishing: useCssVar("--phishing", "#b91c1c"),
    suspicious: useCssVar("--suspicious", "#a3540c"),
    safe: useCssVar("--safe", "#15803d"),
    text: useCssVar("--text", "#1a1917"),
    textMuted: useCssVar("--text-muted", "#6b6860"),
    border: useCssVar("--border", "#ddd9d0"),
    bgRaised: useCssVar("--bg-raised", "#ffffff"),
  };
}
