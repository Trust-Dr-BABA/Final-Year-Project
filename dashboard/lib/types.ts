/**
 * types.ts — TypeScript interface definitions for the dashboard.
 * Matches backend schemas in backend/routers/analyze.py and history.py.
 */

export type Verdict = "phishing" | "suspicious" | "legitimate";

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

export interface Scan {
  scan_id: string;
  url: string;
  verdict: Verdict;
  risk_score: number;
  confidence_pct: number;
  url_features?: Record<string, number | string | boolean>;
  network_signals?: NetworkSignals;
  permission_signals?: PermissionSignals;
  shap_values?: ShapReason[];
  top_reasons?: ShapReason[];
  flagged_rules?: string[];
  created_at: string;
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
