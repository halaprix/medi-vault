"use client";
type Status = "pending" | "processing" | "complete" | "failed";
const colors: Record<Status, string> = { pending: "bg-yellow-100 text-yellow-800", processing: "bg-blue-100 text-blue-800", complete: "bg-green-100 text-green-800", failed: "bg-red-100 text-red-800" };
export function StatusBadge({ status }: { status: Status }) {
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}>{status}</span>;
}
