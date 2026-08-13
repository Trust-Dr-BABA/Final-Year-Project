"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { format } from "date-fns";
import { Scan } from "../lib/types";
import { VerdictBadge } from "./VerdictBadge";

interface HistoryTableProps {
  scans: Scan[];
}

type SortKey = "url" | "verdict" | "risk_pct" | "confidence_pct" | "created_at";

interface ThProps {
  label: string;
  sortBy: SortKey;
  activeSortKey: SortKey;
  sortDesc: boolean;
  onSort: (key: SortKey) => void;
}

// Module-scope, not defined inside HistoryTable — a component declared during another
// component's render is recreated every render, which resets its own state each time.
function Th({ label, sortBy, activeSortKey, sortDesc, onSort }: ThProps) {
  const active = sortBy === activeSortKey;
  return (
    <th
      onClick={() => onSort(sortBy)}
      className="text-left text-[11px] uppercase tracking-wider py-2 px-3 cursor-pointer select-none whitespace-nowrap"
      style={{ color: active ? "var(--text)" : "var(--text-muted)" }}
    >
      {label} {active ? (sortDesc ? "↓" : "↑") : ""}
    </th>
  );
}

// Client-side sortable table for the current page of results — row click opens the scan detail.
export function HistoryTable({ scans }: HistoryTableProps) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDesc, setSortDesc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...scans];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = typeof av === "string" ? av.localeCompare(String(bv)) : Number(av) - Number(bv);
      return sortDesc ? -cmp : cmp;
    });
    return copy;
  }, [scans, sortKey, sortDesc]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDesc((d) => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  if (scans.length === 0) {
    return (
      <p className="text-sm py-8 text-center" style={{ color: "var(--text-muted)" }}>
        No scans recorded yet.
      </p>
    );
  }

  const thProps = { activeSortKey: sortKey, sortDesc, onSort: handleSort };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b" style={{ borderColor: "var(--border)" }}>
            <Th label="URL" sortBy="url" {...thProps} />
            <Th label="Verdict" sortBy="verdict" {...thProps} />
            <Th label="Risk" sortBy="risk_pct" {...thProps} />
            <Th label="Confidence" sortBy="confidence_pct" {...thProps} />
            <Th label="Scanned" sortBy="created_at" {...thProps} />
          </tr>
        </thead>
        <tbody>
          {sorted.map((scan) => (
            <tr
              key={scan.scan_id}
              onClick={() => router.push(`/scan/${scan.scan_id}`)}
              className="border-b cursor-pointer hover:opacity-70 transition-opacity"
              style={{ borderColor: "var(--border)" }}
            >
              <td className="py-2.5 px-3 text-sm max-w-xs truncate" style={{ color: "var(--text)" }} title={scan.url}>
                {scan.url}
              </td>
              <td className="py-2.5 px-3">
                <VerdictBadge verdict={scan.verdict} />
              </td>
              <td className="font-data py-2.5 px-3 text-sm" style={{ color: "var(--text)" }}>
                {scan.risk_pct}%
              </td>
              <td className="font-data py-2.5 px-3 text-sm" style={{ color: "var(--text)" }}>
                {scan.confidence_pct}%
              </td>
              <td className="font-data py-2.5 px-3 text-xs whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
                {format(new Date(scan.created_at), "MMM d, HH:mm")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
