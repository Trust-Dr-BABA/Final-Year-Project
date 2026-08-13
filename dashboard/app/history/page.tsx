import Link from "next/link";
import { getHistory } from "../../lib/api";
import { PageWrapper } from "../../components/layout/PageWrapper";
import { HistoryTable } from "../../components/HistoryTable";

export const revalidate = 0;

const PAGE_SIZE = 25;

// Paginated scan history — server component fetches the page, HistoryTable handles sorting.
export default async function HistoryPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam) || 1);
  const offset = (page - 1) * PAGE_SIZE;

  const { scans, total } = await getHistory(PAGE_SIZE, offset);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <PageWrapper>
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: "var(--text)" }}>
            History
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {total} scan{total === 1 ? "" : "s"} recorded. Click a row for the full explanation.
          </p>
        </div>

        <HistoryTable scans={scans} />

        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm pt-2" style={{ color: "var(--text-muted)" }}>
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-3">
              {page > 1 && (
                <Link href={`/history?page=${page - 1}`} className="hover:opacity-70 transition-opacity" style={{ color: "var(--accent)" }}>
                  ← Previous
                </Link>
              )}
              {page < totalPages && (
                <Link href={`/history?page=${page + 1}`} className="hover:opacity-70 transition-opacity" style={{ color: "var(--accent)" }}>
                  Next →
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
