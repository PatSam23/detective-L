import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Detective-L | AI Research Intelligence",
  description: "Real-time multi-agent research system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
