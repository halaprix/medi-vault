"use client";
export function CardSkeleton() {
  return <div className="rounded-xl border bg-card p-4 animate-pulse"><div className="h-4 bg-muted rounded w-2/3 mb-2" /><div className="h-8 bg-muted rounded w-1/3" /></div>;
}
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return <div className="space-y-2">{[...Array(rows)].map((_, i) => <div key={i} className="h-10 bg-muted rounded animate-pulse" />)}</div>;
}
