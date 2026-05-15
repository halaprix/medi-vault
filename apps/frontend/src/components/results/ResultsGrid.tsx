"use client";
export function ResultsGrid() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      {["Total Cholesterol", "HDL", "LDL", "Triglycerides", "Glucose", "HbA1c"].map(b => (
        <div key={b} className="rounded-xl border bg-card p-3">
          <p className="text-sm font-medium truncate">{b}</p>
          <p className="text-xl font-bold">--</p>
          <p className="text-xs text-muted-foreground">mg/dL</p>
        </div>
      ))}
    </div>
  );
}
