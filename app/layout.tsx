import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Safe Migration — dependency changes, reviewed by people",
  description: "A human-in-the-loop control plane for safe dependency migrations."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
