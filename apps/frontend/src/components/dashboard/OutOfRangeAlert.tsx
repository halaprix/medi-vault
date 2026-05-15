"use client";
export function OutOfRangeAlert() {
  return (
    <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4">
      <p className="font-semibold text-destructive">⚠ Out of Range</p>
      <p className="text-sm text-muted-foreground">Some biomarkers need attention.</p>
    </div>
  );
}
