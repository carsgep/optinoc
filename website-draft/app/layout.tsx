import type { Metadata } from "next";
import { site } from "@/content/site";
import { Navigation, Footer } from "@/components/SiteChrome";
import "./globals.css";
import "./visual-carousel.css";
import "./landings.css";
export const metadata: Metadata = {
  metadataBase: new URL(site.origin),
  title: { default: site.name, template: `%s | ${site.name}` },
  description: site.description,
  robots: { index: !site.draft, follow: !site.draft },
  icons: { icon: "/favicon.svg" },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <Navigation />
        {children}
        <Footer />
      </body>
    </html>
  );
}
