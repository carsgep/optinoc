import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { landings, getLanding } from "@/content/landings";
import { ServiceLanding } from "@/components/ServiceLanding";
import { site } from "@/content/site";
export function generateStaticParams() {
  return landings.map((s) => ({ slug: s.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const s = getLanding(slug);
  if (!s) return {};
  return {
    title: { absolute: s.seoTitle },
    description: s.metaDescription,
    alternates: { canonical: `/soluciones/${slug}/` },
    openGraph: {
      type: "website",
      title: s.headline,
      description: s.description,
      url: `/soluciones/${slug}/`,
      images: [{ url: s.heroSrc, alt: s.alt }],
      locale: "es_CO",
    },
  };
}
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const s = getLanding(slug);
  if (!s) notFound();
  const schema = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: s.name,
    description: s.description,
    url: `${site.origin}/soluciones/${slug}/`,
    provider: { "@type": "Organization", name: site.name, url: site.origin },
  };
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(schema).replace(/</g, "\\u003c"),
        }}
      />
      <ServiceLanding service={s} />
    </>
  );
}
