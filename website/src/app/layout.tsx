import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import { MotionConfig } from "framer-motion";
import { I18nProvider } from "@/lib/i18n";
import {
  SITE_URL,
  SITE_NAME,
  SITE_TITLE,
  TITLE_TEMPLATE,
  SITE_DESCRIPTION,
  OG_IMAGE,
} from "@/lib/metadata";
import { ModalProvider } from "@/components/modals/ModalProvider";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { NpcCityStrip } from "@/components/NpcCityStrip";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  // Without metadataBase, Next.js resolves the relative og-image/twitter-image
  // URLs against http://localhost:3000 in the production build, so social
  // shares of ao.moss.land pointed their preview image at localhost.
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_TITLE,
    template: TITLE_TEMPLATE,
  },
  description: SITE_DESCRIPTION,
  keywords: ["AI", "agents", "orchestrator", "mossland", "crypto", "debate"],
  authors: [{ name: "Mossland" }],
  openGraph: {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    url: SITE_URL,
    siteName: SITE_NAME,
    type: "website",
    images: [OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="theme-color" content="#0a0a0a" />
        <meta name="color-scheme" content="dark" />
      </head>
      <body className={`${jetbrainsMono.variable} font-mono antialiased`}>
        <I18nProvider>
          <MotionConfig reducedMotion="user">
            <ModalProvider>
              <div className="relative min-h-screen bg-[#0a0a0a]">
                <Navigation />
                <main className="relative z-10">
                  {children}
                </main>
                {/* NPC city cross-link — read-side fetch with 10-min
                    revalidate; renders nothing if npc.moss.land is down. */}
                <NpcCityStrip />
                <Footer />
              </div>
            </ModalProvider>
          </MotionConfig>
        </I18nProvider>
      </body>
    </html>
  );
}
