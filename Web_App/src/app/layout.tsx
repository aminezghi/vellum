import type { Metadata } from "next";
import { Figtree, EB_Garamond } from "next/font/google";
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
  title: "Vellum Web — Academic Literature Engine & Research Workspace",
  description: "Free, local-first systematic review workspace by Amine Zouaghi. Multi-source search across 250M+ peer-reviewed papers with Wispr Flow aesthetics.",
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
              try {
                var theme = localStorage.getItem('vellum-theme');
                if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.setAttribute('data-theme', 'dark');
                } else {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.setAttribute('data-theme', 'light');
                }
                var design = localStorage.getItem('vellum-design-style') || 'apple';
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
