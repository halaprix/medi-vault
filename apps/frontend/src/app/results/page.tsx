"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function ResultsPage() {
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    api.get("/results/?per_page=50").then((r) => setResults(r.data)).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">Results</h1>
      <div className="space-y-2">
        {results.map((r: any) => (
          <div
            key={r.id}
            className={`flex items-center justify-between rounded border p-3 ${
              r.is_out_of_range ? "border-red-300 bg-red-50" : "border-gray-200"
            }`}
          >
            <div>
              <p className="font-medium">{r.biomarker_display_name}</p>
              <p className="text-xs text-gray-500">{r.result_date}</p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold">{r.value} <span className="text-sm font-normal text-gray-400">{r.standard_unit}</span></p>
              {r.is_out_of_range && (
                <span className="text-xs text-red-600">{r.out_of_range_direction.toUpperCase()}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
