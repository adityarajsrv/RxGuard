import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geist = Geist({
  variable: "--geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RxGuard",
  description: "Verify medicines against trusted pharmacology sources.",

  icons: {
    icon: [
      {
        url: "/favicon.ico",
        sizes: "any",
      },
      {
        url: "/logo-16x16.png",
        sizes: "16x16",
        type: "image/png",
      },
      {
        url: "/logo-32x32.png",
        sizes: "32x32",
        type: "image/png",
      },
      {
        url: "/logo-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        url: "/logo-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],

    apple: [
      {
        url: "/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`dark ${geist.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-screen flex-col bg-black text-zinc-50">
        {children}
      </body>
    </html>
  );
}