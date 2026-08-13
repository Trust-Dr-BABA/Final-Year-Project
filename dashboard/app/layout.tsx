import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Navbar } from "../components/layout/Navbar";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-family",
});

export const metadata: Metadata = {
  title: "Explainable Security Analyst",
  description:
    "AI-Powered Phishing & Privacy Risk Detection with SHAP Plain-English Explanations",
};

// Applies the persisted theme before paint, so switching themes never flashes the wrong one.
const NO_FLASH_THEME_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("esa-theme");
    var theme = stored === "light" || stored === "dark"
      ? stored
      : (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {}
})();
`;

// App-wide HTML shell: sets fonts, applies the persisted theme before paint, renders the Navbar.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${jetbrainsMono.variable}`}
      // The blocking script below sets data-theme from localStorage, which the server has no way
      // to know in advance — this one, expected, attribute-only mismatch is the standard pattern
      // every SSR dark-mode implementation has (next-themes does the same on this same element).
      suppressHydrationWarning
    >
      <body className="antialiased">
        <Script id="theme-init" strategy="beforeInteractive">
          {NO_FLASH_THEME_SCRIPT}
        </Script>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
