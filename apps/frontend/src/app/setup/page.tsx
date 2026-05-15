"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function SetupPage() {
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [error, setError] = useState("");
  const [step, setStep] = useState<"create" | "confirm">("create");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const getPinStrength = (p: string): { label: string; color: string } => {
    if (p.length < 4) return { label: "Too short", color: "text-red-500" };
    if (p.length < 6) return { label: "Weak", color: "text-orange-500" };
    if (p.length < 8) return { label: "Medium", color: "text-yellow-500" };
    return { label: "Strong", color: "text-green-500" };
  };

  const handleCreatePin = () => {
    if (pin.length < 4) {
      setError("PIN must be at least 4 digits");
      return;
    }
    if (!/^\d+$/.test(pin)) {
      setError("PIN must contain only digits");
      return;
    }
    setError("");
    setStep("confirm");
  };

  const handleSetup = async () => {
    if (pin !== confirmPin) {
      setError("PINs do not match");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/auth/setup", { pin });
      localStorage.setItem("access_token", data.access_token);
      document.cookie = `access_token=${data.access_token}; path=/; max-age=86400; SameSite=Strict`;
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Setup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const strength = getPinStrength(pin);

  return (
    <div className="flex min-h-screen items-center justify-center bg-white dark:bg-gray-950 px-4">
      <div className="w-full max-w-sm space-y-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome to medivault
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {step === "create"
              ? "Create your device PIN to secure your health data"
              : "Confirm your PIN"}
          </p>
        </div>

        {step === "create" ? (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Create PIN (4-8 digits)
              </label>
              <input
                type="password"
                inputMode="numeric"
                maxLength={8}
                value={pin}
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, "");
                  setPin(val);
                  setError("");
                }}
                placeholder="Enter PIN"
                className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-center text-xl tracking-widest text-gray-900 dark:text-white focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none"
                autoFocus
              />
              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium ${strength.color}`}>
                  {strength.label}
                </span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className={`h-1 w-6 rounded-full ${
                        pin.length >= i * 2
                          ? "bg-green-500"
                          : pin.length >= i
                            ? "bg-yellow-400"
                            : "bg-gray-200 dark:bg-gray-700"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}

            <button
              disabled={pin.length < 4}
              onClick={handleCreatePin}
              className="w-full rounded-lg bg-primary px-4 py-3 text-white font-medium hover:bg-primary/90 disabled:opacity-40 transition-colors"
            >
              Continue
            </button>
          </>
        ) : (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Confirm PIN
              </label>
              <input
                type="password"
                inputMode="numeric"
                maxLength={8}
                value={confirmPin}
                onChange={(e) => {
                  setConfirmPin(e.target.value.replace(/\D/g, ""));
                  setError("");
                }}
                placeholder="Re-enter PIN"
                className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-center text-xl tracking-widest text-gray-900 dark:text-white focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none"
                autoFocus
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setStep("create");
                  setConfirmPin("");
                  setError("");
                }}
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 px-4 py-3 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Back
              </button>
              <button
                disabled={confirmPin.length < 4 || loading}
                onClick={handleSetup}
                className="flex-1 rounded-lg bg-primary px-4 py-3 text-white font-medium hover:bg-primary/90 disabled:opacity-40 transition-colors"
              >
                {loading ? "Setting up..." : "Create Account"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
