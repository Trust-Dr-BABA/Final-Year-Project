import { cookies } from "next/headers";
import { getStats } from "../lib/api";
import { PageWrapper } from "../components/layout/PageWrapper";
import { RiskDistributionChart } from "../components/charts/RiskDistributionChart";
import { CLIENT_ID_COOKIE } from "../lib/clientId";

export const revalidate = 0;

// A single stat, label above value, no icon/card chrome — denser than a card grid.
function Stat({
  label,
  value,
  color,
  testId,
}: {
  label: string;
  value: string | number;
  color?: string;
  testId: string;
}) {
  return (
    <div className="border-t-2 pt-3" style={{ borderColor: color ?? "var(--border)" }}>
      <div className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div
        data-testid={testId}
        className="font-data text-3xl font-medium mt-1"
        style={{ color: color ?? "var(--text)" }}
      >
        {value}
      </div>
    </div>
  );
}

// Server component: fetch aggregate stats and render the dashboard overview.
export default async function OverviewPage() {
  const clientId = (await cookies()).get(CLIENT_ID_COOKIE)?.value;
  const stats = await getStats(clientId);

  return (
    <PageWrapper>
      <div className="space-y-10">
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: "var(--text)" }}>
            Overview
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Verdicts and explanations from every page the extension has assessed.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          <Stat label="Total scans" value={stats.total_scans} testId="stat-total-scans" />
          <Stat label="Phishing" value={stats.phishing_count} color="var(--phishing)" testId="stat-phishing" />
          <Stat label="Suspicious" value={stats.suspicious_count} color="var(--suspicious)" testId="stat-suspicious" />
          <Stat label="Legitimate" value={stats.legitimate_count} color="var(--safe)" testId="stat-legitimate" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 border p-5" style={{ borderColor: "var(--border)", borderRadius: "var(--radius)" }}>
            <h2 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
              Verdict distribution
            </h2>
            {stats.total_scans === 0 ? (
              <p data-testid="overview-empty-state" className="text-sm mt-8 mb-8 text-center" style={{ color: "var(--text-muted)" }}>
                {clientId
                  ? "No scans recorded yet. Browse to a page with the extension loaded to start scanning."
                  : "Open this dashboard from the extension popup's \"Open Dashboard\" link to see your own scan history."}
              </p>
            ) : (
              <div className="mt-4" data-testid="risk-distribution-chart">
                <RiskDistributionChart
                  phishingCount={stats.phishing_count}
                  suspiciousCount={stats.suspicious_count}
                  legitimateCount={stats.legitimate_count}
                />
              </div>
            )}
          </div>

          <div className="border p-5 flex flex-col justify-between" style={{ borderColor: "var(--border)", borderRadius: "var(--radius)" }}>
            <div>
              <h2 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
                Average confidence
              </h2>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                Mean decisiveness across all scans — how sure the model was, either direction
                (ADR-015). Not the same quantity as average risk.
              </p>
              <div data-testid="stat-avg-confidence" className="font-data text-4xl font-medium mt-6" style={{ color: "var(--accent)" }}>
                {stats.avg_confidence_pct}%
              </div>
            </div>
            <div className="mt-6 pt-4 border-t text-xs" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
              XGBoost + SHAP TreeExplainer
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
