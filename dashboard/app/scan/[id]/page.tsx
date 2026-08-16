import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { getScan } from "../../../lib/api";
import { CLIENT_ID_COOKIE } from "../../../lib/clientId";
import { VERDICT_COLOR } from "../../../lib/types";
import { PageWrapper } from "../../../components/layout/PageWrapper";
import { VerdictBadge } from "../../../components/VerdictBadge";
import { ConfidenceBadge } from "../../../components/ConfidenceBadge";
import { ShapWaterfallChart } from "../../../components/charts/ShapWaterfallChart";

export const revalidate = 0;

const VT_COLOR = "var(--text-muted)"; // corroboration, never colours the verdict — ADR-013

// VT corroboration never changes the verdict (ADR-013), but a visible disagreement is worth
// surfacing: it tells the user VT's own reputation data doesn't line up with this system's own
// assessment, without making VT the thing that decided the verdict.
function vtDisagreement(
  verdict: string,
  maliciousVotes: number,
  harmlessVotes: number
): string | null {
  if (maliciousVotes > 0 && verdict !== "phishing") {
    return `VirusTotal has ${maliciousVotes} vendor(s) flagging this domain as malicious, though this system's own assessment is "${verdict}".`;
  }
  if (verdict === "phishing" && maliciousVotes === 0 && harmlessVotes > 0) {
    return `VirusTotal has no vendors flagging this domain (${harmlessVotes} report it as clean), though this system's own assessment is "phishing".`;
  }
  return null;
}

function Card({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`border p-5 ${className}`} style={{ borderColor: "var(--border)", borderRadius: "var(--radius)" }}>
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

// Full detail for one scan: verdict, risk bar, network/permission/content/VT cards, SHAP chart.
// One row per (client_id, url) — re-scanning a URL updates this same record rather than adding a
// new one, so there's no "risk trend over time" here any more (that chart is retired: it can only
// ever show a single point now, since there's only ever one row per URL per browser).
export default async function ScanDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const clientId = (await cookies()).get(CLIENT_ID_COOKIE)?.value;
  const scan = await getScan(id, clientId);
  if (!scan) notFound();

  const reasons = scan.shap_values ?? [];
  const network = scan.network_signals;
  const permissions = scan.permission_signals;
  const scamContent = scan.scam_content_signals;
  const features = scan.url_features ?? {};
  // VT is fetched synchronously before scoring (backend/routers/analyze.py). vt_malicious_votes
  // always feeds the fused score (risk_fusion.py's asymmetric weight); vt_harmless_votes only does
  // when domain_age_days/vt_malicious_votes/vt_harmless_votes jointly clear the gated
  // established-reputation threshold (see fuse()) — a brand-new phishing domain cannot satisfy
  // that gate. The columns still default to -1 whenever VT has no key configured, times out, or
  // errors, so presence in url_features still isn't the same as success; only the value is.
  const vtMalicious = Number(features.vt_malicious_votes ?? -1);
  const vtHarmless = Number(features.vt_harmless_votes ?? -1);
  const vtDomainAge = Number(features.domain_age_days ?? -1);
  const hasVt = vtMalicious !== -1 || vtHarmless !== -1 || vtDomainAge !== -1;
  const disagreement = hasVt ? vtDisagreement(scan.verdict, vtMalicious, vtHarmless) : null;

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
          <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
            First scanned {new Date(scan.created_at).toLocaleString()}
            {scan.last_scanned_at && scan.last_scanned_at !== scan.created_at && (
              <> · last re-checked {new Date(scan.last_scanned_at).toLocaleString()}</>
            )}
          </p>
        </div>

        {/* Risk bar */}
        <div data-testid="risk-bar">
          <div className="flex justify-between text-xs mb-1" style={{ color: "var(--text-muted)" }}>
            <span>Risk score</span>
            <span data-testid="risk-pct" className="font-data">{scan.risk_pct}%</span>
          </div>
          <div className="h-2 w-full" style={{ backgroundColor: "var(--border)", borderRadius: "var(--radius)" }}>
            <div
              className="h-2"
              style={{
                width: `${scan.risk_pct}%`,
                backgroundColor: VERDICT_COLOR[scan.verdict],
                borderRadius: "var(--radius)",
              }}
            />
          </div>
        </div>

        <Card title="Why this verdict">
          <div data-testid="shap-waterfall-chart">
            <ShapWaterfallChart reasons={reasons} />
          </div>
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

          <Card title="Page content signals" className="md:col-span-2">
            {scamContent && (scamContent.matched_phrases?.length ?? 0) > 0 ? (
              <div className="mb-3">
                <p className="text-sm mb-2" style={{ color: "var(--text)" }}>
                  {scamContent.scam_keyword_hits} scam-indicator phrase(s) found in the page text:
                </p>
                <ul className="text-sm space-y-1.5" style={{ color: "var(--text)" }}>
                  {scamContent.matched_phrases!.map((phrase) => (
                    <li key={phrase}>• {phrase}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm mb-3" style={{ color: "var(--text-muted)" }}>No scam-indicator phrases detected on this page.</p>
            )}
            {scamContent && (scamContent.sensitive_field_categories?.length ?? 0) > 0 ? (
              <div className="pt-3 border-t" style={{ borderColor: "var(--border)" }}>
                <p className="text-sm mb-2" style={{ color: "var(--text)" }}>
                  {scamContent.sensitive_field_count} categories of sensitive form fields requested:
                </p>
                <ul className="text-sm space-y-1.5" style={{ color: "var(--text)" }}>
                  {scamContent.sensitive_field_categories!.map((category) => (
                    <li key={category}>• {category.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm pt-3 border-t" style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}>
                No sensitive form-field categories detected on this page.
              </p>
            )}
          </Card>
        </div>

        <Card title="VirusTotal corroboration">
          <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
            Never a trained model feature (ADR-013 — the training corpus overlaps with what VT
            ingests, which would be circular). Since 2026-08-15, vendors actively flagging a domain
            malicious raises the score above. A clean or unavailable result here does not lower it
            by default — except when the domain is long-registered (1+ year) AND has 10+ vendors
            reporting it harmless with zero flagging it malicious, which a brand-new phishing domain
            cannot fake — see "Why this verdict" above for whether either was a factor in this scan.
          </p>
          {hasVt ? (
            <div>
              <div style={{ color: VT_COLOR }}>
                <Field label="Domain age (days)" value={vtDomainAge === -1 ? "—" : String(vtDomainAge)} />
                <Field label="Vendors flagging malicious" value={vtMalicious === -1 ? "—" : String(vtMalicious)} />
                <Field label="Vendors flagging harmless" value={vtHarmless === -1 ? "—" : String(vtHarmless)} />
              </div>
              {disagreement && (
                <p className="text-xs mt-3 pt-3 border-t" style={{ color: "var(--suspicious)", borderColor: "var(--border)" }}>
                  ⚠ {disagreement}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Unavailable for this scan — no API key configured, VirusTotal timed out, or it returned
              no data for this domain.
            </p>
          )}
        </Card>
      </div>
    </PageWrapper>
  );
}
