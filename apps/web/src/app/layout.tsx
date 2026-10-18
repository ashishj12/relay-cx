import type { Metadata } from "next";
import "@fontsource-variable/dm-sans";
import "@fontsource-variable/newsreader";
import "./globals.css";
export const metadata: Metadata = {
  title: "Relay — Connected to a resolution",
  description:
    "Verified telecom support, clear conversations, and resolutions you can trace.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
