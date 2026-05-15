"use client";
export function MetricsTrendChart({ metric }: { metric?: string }) {
  return <div className="rounded-xl border bg-card p-4"><h3 className="font-semibold mb-2">{metric || "Metric"} Trend</h3><div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Chart placeholder</div></div>;
}
