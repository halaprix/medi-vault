"use client";
const categories = ["Lipid Panel", "Metabolic", "CBC", "Thyroid", "Vitamins"];
export function CategoryHealthCards() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {categories.map(cat => (
        <div key={cat} className="rounded-xl border bg-card p-3 text-center">
          <p className="text-sm font-medium">{cat}</p>
          <p className="text-xs text-muted-foreground">--</p>
        </div>
      ))}
    </div>
  );
}
