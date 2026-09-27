import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GEOAI-AU | Mineral Prospectivity Intelligence (España Peninsular)",
  description: "Plataforma geoespacial interactiva de prospectividad aurífera para España peninsular basada en GeoAI-Au v1.0.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="h-full w-full bg-slate-950 text-slate-100 overflow-hidden font-sans">
        {children}
      </body>
    </html>
  );
}
