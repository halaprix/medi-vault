"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function LoginPage() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const { data } = await api.post("/auth/login", { pin });
      localStorage.setItem("access_token", data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Incorrect PIN");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-4 rounded-lg border p-8">
        <h1 className="text-2xl font-bold">medi-vault</h1>
        <input
          type="password"
          maxLength={8}
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          placeholder="Enter PIN"
          className="w-full rounded border px-3 py-2"
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        <button
          disabled={pin.length < 4}
          onClick={handleLogin}
          className="w-full rounded bg-primary px-4 py-2 text-white disabled:opacity-50"
        >
          Unlock
        </button>
      </div>
    </div>
  );
}
