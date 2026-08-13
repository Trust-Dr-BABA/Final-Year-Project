import { notFound } from "next/navigation";
import { getScan, getHistory } from "../../../lib/api";
import { PageWrapper } from "../../../components/layout/PageWrapper";
import { VerdictBadge } from "../../../components/VerdictBadge";
import { ConfidenceBadge } from "../../../components/ConfidenceBadge";
import { ShapWaterfallChart } from "../../../components/charts/ShapWaterfallChart";
import { RiskSparkline } from "../../../components/charts/RiskSparkline";

export const revalidate = 0;

const VT_COLOR = "var(--text-muted)"; // corroboration, never colours the verdict — ADR-013

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border p-5" style={{ borderColor: "var(--border)", borderRadius: "var(--radius)" }}>
      <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between text-sm py-1.5 border-b last:border-0" style={{ borderColor: "var(--border)" }}>
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="font-data" style={{ color: "var(--text)" }}>{value}</span>
    </div>
  );
}

// Full detail for one scan: verdict, risk bar, network/permission/VT cards, SHAP chart, trend.
export default async function ScanDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const scan = await getScan(id);
  if (!scan) notFound();

  const reasons = scan.shap_values ?? scan.top_reasons ?? [];
  const network = scan.network_signals;
  const permissions = scan.permission_signals;
  const features = scan.url_features ?? {};
  const hasVt = "domain_age_days" in features;

  // Same-URL history for the trend chart — fetched broad and filtered, since /history has no
  // per-URL filter (a real gap; acceptable for a research-scale demo dataset).
  const { scans: recent } = await getHistory(200, 0);
  const sameUrlScans = recent.filter((s) => s.url === scan.url);

  return (
    <PageWrapper>
      <div className="space-y-6">
        <div>
          <p className="font-data text-sm break-all" style={{ color: "var(--text-muted)" }}>
            {scan.url}
          </p>
          <div className="flex items-center gap-3 mt-3">
            <VerdictBadge verdict={scan.verdict} className="text-sm px-3 py-1" />
            <ConfidenceBadge confidencePct={scan.confidence_pct} verdict={scan.verdict} />
          </div>
        </div>

        {/* Risk bar */}
        <div>
          <div className="flex justify-between text-xs mb-1" style={{ color: "var(--text-muted)" }}>
            <span>Risk score</span>
            <span className="font-data">{scan.risk_pct}%</span>
          </div>
          <div className="h-2 w-full" style={{ backgroundColor: "var(--border)", borderRadius: "var(--radius)" }}>
            <div
              className="h-2"
              style={{
                width: `${scan.risk_pct}%`,
                backgroundColor:
                  scan.verdict === "phishing" ? "var(--phishing)" : scan.verdict === "suspicious" ? "var(--suspicious)" : "var(--safe)",
                borderRadius: "var(--radius)",
              }}
            />
          </div>
        </div>

        <Card title="Why this verdict">
          <ShapWaterfallChart reasons={reasons} />
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card title="Network signals">
            {network ? (
              <div>
                <Field label="Third-party trackers" value={network.tracker_count ?? 0} />
                <Field label="Mixed content" value={network.has_mixed_content ? "Yes" : "No"} />
                <Field label="Redirect chain length" value={network.redirect_chain_length ?? 0} />
              </div>
            ) : (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No network signals recorded.</p>
            )}
          </Card>

          <Card title="Permission signals">
            {permissions && (permissions.rule_flags?.length ?? 0) > 0 ? (
              <ul className="text-sm space-y-1.5" style={{ color: "var(--text)" }}>
                {permissions.rule_flags!.map((flag) => (
                  <li key={flag}>• {flag.replace(/_/g, " ")}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No permission signals flagged.</p>
            )}
          </Card>
        </div>

        <Card title="VirusTotal corroboration">
          <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
            Shown for context only — never a trained feature, and never changes the verdict above (ADR-013).
          </p>
          {hasVt ? (
            <div style={{ color: VT_COLOR }}>
              <Field label="Domain age (days)" value={String(features.domain_age_days ?? "—")} />
              <Field label="Vendors flagging malicious" value={String(features.vt_malicious_votes ?? "—")} />
              <Field label="Vendors flagging harmless" value={String(features.vt_harmless_votes ?? "—")} />
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>Unavailable for this scan.</p>
          )}
        </Card>

        <Card title="Risk trend for this URL">
          <RiskSparkline scans={sameUrlScans} />
        </Card>
      </div>
    </PageWrapper>
  );
}
