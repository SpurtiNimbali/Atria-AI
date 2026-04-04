import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EHR Copilot - Voice-First Clinical Assistant",
  description: "Voice-first clinician copilot with EHR context",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, height: "100vh", overflow: "hidden" }}>{children}</body>
    </html>
  );
}
