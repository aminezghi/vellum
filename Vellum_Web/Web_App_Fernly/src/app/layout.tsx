import type { Metadata } from "next";
import { LEGACY_STORAGE_BOOT, STORAGE_KEYS } from "@/lib/storageNamespace";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vellum by Amine — Academic Research Studio",
  description: "A private, local-first academic research studio. Systematic reviews, multi-source search across 250M+ papers, citation mapping, and deep appraisal.",
  authors: [{ name: "Amine Zouaghi" }],
  creator: "Amine Zouaghi",
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
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
        className="font-sans antialiased min-h-screen transition-colors duration-250"
      >
        {children}
      </body>
    </html>
  );
}
