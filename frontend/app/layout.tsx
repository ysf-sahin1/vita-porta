import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vita Porta — Triaj Asistanı",
  description:
    "Acil servis girişinde hemşireye gerekçeli triaj önerisi sunan multi-agent yapay zekâ asistanı.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body className="font-sans text-slate-900 antialiased">{children}</body>
    </html>
  );
}
