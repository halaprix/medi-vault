"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function SetupPage() {
  const [pin, setPin] = useState("");
  const router = useRouter();

  const handleSetup = async () => {
    try {
      const { data } = await api.post("/auth/setup", { pin });
      localStorage.setItem("access_token", data.access_token);
      router.push("/dashboard");
    } catch {
      alert("Setup failed");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-4 rounded-lg border p-8">
        <h1 className="text-2xl font-bold">Welcome to medi-vault</h1>
        <p className="text-sm text-gray-500">Set up your local PIN to protect your health data.</p>
        <input
          type="password"
          maxLength={8}
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          placeholder="4-8 digit PIN"
          className="w-full rounded border px-3 py-2"
        />
        <button
          disabled={pin.length < 4}
          onClick={handleSetup}
          className="w-full rounded bg-primary px-4 py-2 text-white disabled:opacity-50"
        >
          Set PIN & Continue
        </button>
      </div>
    </div>
  );
}
