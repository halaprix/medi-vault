import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "medi-vault — Health Analytics",
  description: "Privacy-first local health data analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <div>TEST BANNER</div>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
