/**
 * types.ts — TypeScript interface definitions for the dashboard.
 * Matches backend schemas in backend/routers/analyze.py and history.py.
 */

export type Verdict = "phishing" | "suspicious" | "legitimate";

// Single source of truth for verdict → color, previously redefined independently in
// VerdictBadge, ConfidenceBadge, and the scan detail page's risk bar.
export const VERDICT_COLOR: Record<Verdict, string> = {
  phishing: "var(--phishing)",
  suspicious: "var(--suspicious)",
  legitimate: "var(--safe)",
};

export interface ShapReason {
  feature: string;
  value: number | boolean | string | null;
  shap_impact: number;
  human_readable: string;
}

export interface NetworkSignals {
  tracker_count?: number;
  has_mixed_content?: boolean;
  redirect_chain_length?: number;
  third_party_domains?: string[];
}

export interface PermissionSignals {
  permissions_requested?: string[];
  rule_flags?: string[];
}

export interface ScamContentSignals {
  scam_keyword_hits?: number;
  matched_phrases?: string[];
  sensitive_field_count?: number;
  sensitive_field_categories?: string[];
}

export interface Scan {
  scan_id: string;
  url: string;
  verdict: Verdict;
  risk_score: number;
  risk_pct: number;        // round(risk_score * 100) — how phishing-like the page is (ADR-015)
  confidence_pct: number;  // round(max(p, 1-p) * 100) — how decisive the model is (ADR-015)
  url_features?: Record<string, number | string | boolean>;
  network_signals?: NetworkSignals;
  permission_signals?: PermissionSignals;
  scam_content_signals?: ScamContentSignals;
  shap_values?: ShapReason[];
  flagged_rules?: string[];
  created_at: string;
  last_scanned_at: string;
}

export interface HistoryResponse {
  scans: Scan[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  total_scans: number;
  phishing_count: number;
  suspicious_count: number;
  legitimate_count: number;
  avg_confidence_pct: number;
}
