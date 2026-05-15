"use client";
export function MetricsSummaryBar() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {["Total Docs", "Out of Range", "Healthy", "Pending"].map(label => (
        <div key={label} className="rounded-xl border bg-card p-4">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold">--</p>
        </div>
      ))}
    </div>
  );
}
