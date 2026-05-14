import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "medi-vault — Health Analytics",
  description: "Privacy-first local health data analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
