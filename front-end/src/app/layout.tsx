import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sri Lanka IRD Tax Intelligence & Compliance Assistant",
  description: "Intelligent Tax Assistant powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
