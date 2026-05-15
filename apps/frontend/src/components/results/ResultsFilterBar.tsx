"use client";
export function ResultsFilterBar() {
  return (
    <div className="flex gap-2 flex-wrap items-center">
      <input placeholder="Search..." className="rounded-lg border px-3 py-1.5 text-sm" />
      <select className="rounded-lg border px-3 py-1.5 text-sm"><option>All Categories</option></select>
      <select className="rounded-lg border px-3 py-1.5 text-sm"><option>All Status</option></select>
    </div>
  );
}
