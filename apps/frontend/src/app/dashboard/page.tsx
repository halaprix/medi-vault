"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<any[]>([]);
  const [outOfRange, setOutOfRange] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    api.get("/results/summary").then((r) => setSummary(r.data)).catch(() => {});
    api.get("/results/out-of-range").then((r) => setOutOfRange(r.data)).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-primary">medi-vault</h1>
        <button onClick={() => router.push("/upload")}
          className="rounded bg-accent px-4 py-2 text-white">
          Upload Lab Results
        </button>
      </header>

      {outOfRange.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-semibold text-red-800">
            {outOfRange.length} biomarkers out of range
          </p>
          <ul className="mt-2 text-sm text-red-700">
            {outOfRange.slice(0, 3).map((r: any) => (
              <li key={r.biomarker_id}>
                {r.display_name}: {r.value} {r.unit} ({r.direction})
              </li>
            ))}
          </ul>
        </div>
      )}

      <section>
        <h2 className="mb-3 text-xl font-semibold">Latest Results</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {summary.slice(0, 12).map((r: any) => (
            <div
              key={r.biomarker_id}
              className={`rounded-lg border p-4 ${
                r.is_out_of_range ? "border-red-300 bg-red-50" : "border-gray-200"
              }`}
            >
              <p className="text-sm text-gray-500">{r.display_name}</p>
              <p className="text-2xl font-bold">{r.latest_value}</p>
              <p className="text-xs text-gray-400">{r.unit}</p>
            </div>
          ))}
        </div>
      </section>

      <nav className="fixed bottom-0 left-0 right-0 flex justify-around border-t bg-white p-3 md:static md:border-t-0">
        {["Dashboard", "Upload", "Results", "Settings"].map((label) => (
          <button
            key={label}
            onClick={() => router.push(`/${label.toLowerCase()}`)}
            className="text-sm text-gray-600"
          >
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}
