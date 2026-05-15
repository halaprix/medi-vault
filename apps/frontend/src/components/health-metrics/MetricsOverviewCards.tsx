"use client";
export function MetricsOverviewCards() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {["Weight", "Steps", "Sleep", "Resting HR"].map(m => (
        <div key={m} className="rounded-xl border bg-card p-3">
          <p className="text-sm text-muted-foreground">{m}</p>
          <p className="text-xl font-bold">--</p>
        </div>
      ))}
    </div>
  );
}
