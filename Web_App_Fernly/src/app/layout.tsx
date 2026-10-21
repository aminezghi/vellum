import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import { LEGACY_STORAGE_BOOT, STORAGE_KEYS } from "@/lib/storageNamespace";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vellum — Fernly Botanical Bento Edition",
  description: "A calm, organic botanical academic workspace that moves as one product. Systematic reviews, multi-source search across 250M+ papers, and deep appraisal.",
  authors: [{ name: "Amine Zouaghi" }],
  creator: "Amine Zouaghi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              ${LEGACY_STORAGE_BOOT}
              try {
                var theme = localStorage.getItem('${STORAGE_KEYS.theme}');
                if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.setAttribute('data-theme', 'dark');
                } else {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.setAttribute('data-theme', 'light');
                }
                var accent = localStorage.getItem('${STORAGE_KEYS.accent}') || 'emerald';
                document.documentElement.setAttribute('data-accent', accent);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body
        className={`${plusJakartaSans.variable} font-sans antialiased min-h-screen transition-colors duration-250`}
      >
        {children}
      </body>
    </html>
  );
}
