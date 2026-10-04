import Link from "next/link";
import { site } from "@/content/site";
import { MediaBlock } from "./MediaBlock";
import { ContactButton } from "./SiteChrome";
export function Hero() {
  return (
    <section className="hero shell">
      <div className="hero-copy">
        <p className="eyebrow">{site.hero.eyebrow}</p>
        <h1>
          {site.hero.lines.map((line, i) => (
            <span key={line} className={i === 2 ? "accent" : ""}>
              {line}
            </span>
          ))}
        </h1>
        <p className="hero-lead">{site.hero.lead}</p>
        <p className="hero-description">{site.description}</p>
        <div className="hero-actions">
          <Link className="button primary" href="#soluciones">
            {site.hero.primary}
          </Link>
          <ContactButton
            label={site.hero.secondary}
            location="hero"
            secondary
          />
        </div>
      </div>
      <div className="hero-visual">
        {site.heroMedia ? (
          <MediaBlock media={site.heroMedia} priority />
        ) : (
          <div className="business-diagram" aria-label={site.hero.diagramTitle}>
            <div className="diagram-heading">
              <span className="diagram-cross" aria-hidden="true">
                +
              </span>
              {site.hero.diagramTitle}
              <span className="diagram-cross" aria-hidden="true">
                +
              </span>
            </div>
            <div className="diagram-rings" aria-hidden="true">
              <div />
              <div />
              <div />
            </div>
            <div className="diagram-core">
              <span>{site.name.toUpperCase()}</span>
              <strong>{site.hero.diagramCore}</strong>
            </div>
            {site.hero.diagramNodes.map((n, i) => (
              <div key={n} className={`diagram-node node-${i}`}>
                <span>{String(i + 1).padStart(2, "0")}</span>
                <strong>{n}</strong>
              </div>
            ))}
            <p className="diagram-caption">{site.hero.diagramCaption}</p>
          </div>
        )}
      </div>
      <div className="hero-bottom">
        {site.heroFooter.map((text) => (
          <span key={text}>{text}</span>
        ))}
      </div>
    </section>
  );
}
