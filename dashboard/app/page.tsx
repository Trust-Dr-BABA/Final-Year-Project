import { getStats } from "../lib/api";
import { PageWrapper } from "../components/layout/PageWrapper";

export const revalidate = 0;

// Server component: fetch aggregate stats and render the dashboard overview cards.
export default async function OverviewPage() {
  const stats = await getStats();

  return (
    <PageWrapper>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Security & Privacy Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time analytics and threat statistics from Chrome extension page scans.
          </p>
        </div>

        {/* Stat Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#1a1a2e] border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Scans
            </div>
            <div className="text-3xl font-extrabold text-slate-100 mt-2">
              {stats.total_scans}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              URLs analyzed to date
            </p>
          </div>

          <div className="bg-[#1a1a2e] border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="text-xs font-semibold text-red-400 uppercase tracking-wider">
              Phishing Detected
            </div>
            <div className="text-3xl font-extrabold text-red-400 mt-2">
              {stats.phishing_count}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              High risk score (&gt; 70%)
            </p>
          </div>

          <div className="bg-[#1a1a2e] border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              Suspicious Sites
            </div>
            <div className="text-3xl font-extrabold text-amber-400 mt-2">
              {stats.suspicious_count}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Moderate risk score (40–70%)
            </p>
          </div>

          <div className="bg-[#1a1a2e] border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="text-xs font-semibold text-green-400 uppercase tracking-wider">
              Legitimate Sites
            </div>
            <div className="text-3xl font-extrabold text-green-400 mt-2">
              {stats.legitimate_count}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Safe score (&lt; 40%)
            </p>
          </div>
        </div>

        {/* Secondary Info Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-[#1a1a2e] border border-slate-800 rounded-xl p-6">
            <h2 className="text-base font-semibold text-slate-200">
              Risk Distribution Breakdown
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Distribution of verdicts processed by the XGBoost & SHAP analysis engine.
            </p>

            <div className="h-48 flex items-center justify-center border border-dashed border-slate-800 rounded-lg mt-4 text-sm text-slate-500">
              {stats.total_scans === 0
                ? "No scans recorded yet. Load the Chrome extension to start scanning."
                : `Total Scans: ${stats.total_scans} (${stats.phishing_count} Phishing, ${stats.suspicious_count} Suspicious, ${stats.legitimate_count} Legitimate)`}
            </div>
          </div>

          <div className="bg-[#1a1a2e] border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-200">
                Average Confidence Score
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Mean model confidence across all processed scans.
              </p>
              <div className="text-4xl font-extrabold text-indigo-400 mt-6">
                {stats.avg_confidence_pct}%
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800">
              <span className="text-xs text-slate-400">
                Model: XGBoost + SHAP TreeExplainer
              </span>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
