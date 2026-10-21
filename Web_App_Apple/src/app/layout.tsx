import type { Metadata } from "next";
import { Figtree, EB_Garamond } from "next/font/google";
import { LEGACY_STORAGE_BOOT, STORAGE_KEYS } from "@/lib/storageNamespace";
import "./globals.css";

const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

const ebGaramond = EB_Garamond({
  variable: "--font-garamond",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vellum Web (Apple Design Edition) — Fluid Academic Literature Engine",
  description: "Free, local-first systematic review workspace by Amine Zouaghi. Engineered with Apple Design principles, Cupertino frosted vibrancy, fluid spring physics, and continuous squircle geometry.",
  authors: [{ name: "Amine Zouaghi" }],
  creator: "Amine Zouaghi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-design="apple" suppressHydrationWarning>
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
                var design = localStorage.getItem('${STORAGE_KEYS.designStyle}') || 'apple';
                document.documentElement.setAttribute('data-design', design);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body
        className={`${figtree.variable} ${ebGaramond.variable} font-sans antialiased min-h-screen transition-colors duration-200`}
      >
        {children}
      </body>
    </html>
  );
}
