import type { Metadata } from "next";
import { site } from "@/content/site";
import { corporateMetrics, cases, technologies } from "@/content/solutions";
import { SolutionsExperience } from "@/components/SolutionsExperience";
import { ExperienceMetrics, SuccessCaseCard } from "@/components/Story";
import { CTASection } from "@/components/SiteChrome";
import { MediaBlock } from "@/components/MediaBlock";
export const metadata: Metadata = {
  title: "Proteger, operar y transformar",
  description: site.description,
  alternates: { canonical: "/home-v2/" },
  openGraph: {
    type: "website",
    locale: "es_CO",
    title: site.title,
    description: site.description,
    url: "/home-v2/",
  },
};
export default function Home() {
  return (
    <main id="contenido">
      <SolutionsExperience />
      <section id="experiencia" className="experience-section">
        <div className="shell">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{site.labels.experienceEyebrow}</p>
              <h2>{site.labels.experienceTitle}</h2>
            </div>
            <p>{site.labels.experienceDescription}</p>
          </div>
          <ExperienceMetrics items={corporateMetrics} />
          <p className="metric-note">{site.labels.metricNote}</p>
        </div>
      </section>
      <section id="casos" className="cases-section shell">
        <p className="eyebrow">{site.labels.caseEyebrow}</p>
        <h2>{site.labels.caseTitle}</h2>
        <div className="case-grid">
          {cases
            .filter((c) => !c.requiresValidation)
            .map((c) => (
              <SuccessCaseCard item={c} key={c.id} />
            ))}
        </div>
      </section>
      <section className="partners shell">
        <p className="eyebrow">{site.labels.partnerEyebrow}</p>
        <h2>{site.labels.partnerTitle}</h2>
        <p>{site.labels.partnerDescription}</p>
        <div className="technology-grid">
          {technologies.map((t) => (
            <div key={t.name}>
              {t.logo ? <MediaBlock media={t.logo} /> : <span>{t.name}</span>}
            </div>
          ))}
        </div>
      </section>
      <section id="nosotros" className="about shell">
        <p className="eyebrow">{site.name}</p>
        <h2>{site.labels.aboutTitle}</h2>
        <p>{site.labels.aboutDescription}</p>
      </section>
      <CTASection />
    </main>
  );
}
