import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { solutions } from "@/content/solutions";
import { site } from "@/content/site";
import { SolutionStory } from "@/components/Story";
import { ContactButton, CTASection } from "@/components/SiteChrome";
export function generateStaticParams() {
  return solutions.map((s) => ({ slug: s.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const s = solutions.find((s) => s.slug === slug);
  if (!s) return {};
  return {
    title: s.name,
    description: s.description,
    alternates: { canonical: `/soluciones/${slug}/` },
    openGraph: {
      type: "website",
      title: s.name,
      description: s.description,
      url: `/soluciones/${slug}/`,
      locale: "es_CO",
    },
  };
}
export default async function SolutionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const s = solutions.find((s) => s.slug === slug);
  if (!s) notFound();
  const structured = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: s.name,
    description: s.description,
    url: `${site.origin}/soluciones/${slug}/`,
    provider: { "@type": "Organization", name: site.name, url: site.origin },
  };
  return (
    <main id="contenido">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structured).replace(/</g, "\\u003c"),
        }}
      />
      <section className="detail-hero shell">
        <Link href="/home-v2/#soluciones">{site.labels.back}</Link>
        <p className="eyebrow">{s.name}</p>
        <h1>{s.tagline}</h1>
        <p>{s.description}</p>
        <ContactButton label={s.cta} location={`${s.slug}:detail`} />
        <nav className="detail-nav" aria-label={s.name}>
          {site.labels.steps.map((label, i) => (
            <a key={label} href={`#etapa-${i}`}>
              {label}
            </a>
          ))}
        </nav>
      </section>
      <div className="shell detail-stories">
        {site.labels.steps.map((label, i) => (
          <section
            id={`etapa-${i}`}
            key={label}
            aria-labelledby={`heading-${i}`}
          >
            <h2 id={`heading-${i}`}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              {label}
            </h2>
            <SolutionStory solution={s} step={i} />
          </section>
        ))}
        <aside className="references">
          <h2>{site.labels.sources}</h2>
          {s.references.map((r) => (
            <a
              key={r.url}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {r.label}
            </a>
          ))}
        </aside>
      </div>
      <CTASection />
    </main>
  );
}
