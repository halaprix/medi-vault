"use client";
import { useTheme } from "@/components/ThemeProvider";
export function GeneralSettings() {
  const { theme, setTheme } = useTheme();
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">General</h3>
      <div className="flex items-center justify-between">
        <span className="text-sm">Theme</span>
        <select value={theme} onChange={e => setTheme(e.target.value as any)} className="rounded-lg border px-3 py-1.5 text-sm">
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
    </div>
  );
}
