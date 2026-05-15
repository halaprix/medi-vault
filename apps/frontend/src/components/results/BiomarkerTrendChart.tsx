"use client";
export function BiomarkerTrendChart({ biomarkerId }: { biomarkerId?: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="font-semibold mb-2">Trend: {biomarkerId || "Select biomarker"}</h3>
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        Chart — Recharts LineChart
      </div>
      <div className="flex gap-2 mt-2">
        <button className="text-xs px-2 py-1 rounded bg-secondary">Zoom</button>
        <button className="text-xs px-2 py-1 rounded bg-secondary">Overlay</button>
      </div>
    </div>
  );
}
