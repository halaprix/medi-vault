"use client";
import Link from "next/link";
export function QuickActions() {
  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="font-semibold mb-2">Quick Actions</h3>
      <div className="flex gap-2 flex-wrap">
        <Link href="/upload" className="rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm">Upload</Link>
        <Link href="/results" className="rounded-lg bg-secondary text-secondary-foreground px-4 py-2 text-sm">View Results</Link>
      </div>
    </div>
  );
}
