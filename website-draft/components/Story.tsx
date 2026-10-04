import type {
  Evidence,
  Metric,
  Solution,
  SuccessCase,
} from "@/content/solutions";
import { site } from "@/content/site";
import { ContactButton } from "./SiteChrome";
import { MediaBlock } from "./MediaBlock";
import { CaseObserver } from "./Tracking";
export function MarketEvidence({ items }: { items: Evidence[] }) {
  return (
    <div className="evidence-grid">
      {items.map((item) => (
        <article className="evidence" key={item.label}>
          <strong>{item.value}</strong>
          <h4>{item.label}</h4>
          <p>{item.context}</p>
          <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">
            {site.labels.source}: {item.source}, {item.publicationYear}
          </a>
        </article>
      ))}
    </div>
  );
}
export function ExperienceMetrics({ items }: { items: Metric[] }) {
  return (
    <div className="metrics">
      {items.map((m) => (
        <div key={m.label}>
          <strong>{m.value}</strong>
          <span>{m.label}</span>
        </div>
      ))}
    </div>
  );
}
export function SuccessCaseCard({ item }: { item: SuccessCase }) {
  return (
    <CaseObserver id={item.id}>
      <article className="case-card">
        {item.logo && (
          <div className="case-logo">
            <MediaBlock media={item.logo} />
          </div>
        )}
        <p className="eyebrow">{item.clientName || item.sector}</p>
        <h3>{item.title}</h3>
        {item.requiresValidation && (
          <small className="review-label">{site.labels.casePending}</small>
        )}
        <dl>
          {[
            [site.labels.caseChallenge, item.challenge],
            [site.labels.caseSolution, item.solution],
            [site.labels.caseResult, item.result],
          ].map(([term, value]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <div className="tags">
          {item.technologies.map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>
      </article>
    </CaseObserver>
  );
}
export function SolutionStory({
  solution: s,
  step,
}: {
  solution: Solution;
  step: number;
}) {
  if (step === 0)
    return (
      <div className="story-challenge">
        <div>
          <p className="eyebrow">{site.labels.steps[0]}</p>
          <h3>{s.tagline}</h3>
          <p>{s.problem}</p>
        </div>
        <MarketEvidence items={s.evidence} />
      </div>
    );
  if (step === 1)
    return (
      <div>
        <p className="story-intro">{s.proposal}</p>
        <div className="capabilities">
          {s.capabilities.map((c, i) => (
            <article key={c.title}>
              <span className="cap-index">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h4>{c.title}</h4>
              <p>{c.description}</p>
            </article>
          ))}
        </div>
        <p className="eyebrow tech-label">{site.labels.technologies}</p>
        <div className="tags">
          {s.technologies.map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>
      </div>
    );
  if (step === 2)
    return (
      <div className="experience-story">
        <p className="story-intro">{s.experience}</p>
        {s.metrics.length > 0 && (
          <>
            <ExperienceMetrics items={s.metrics} />
            <small>{site.labels.metricNote}</small>
          </>
        )}
        {s.media && <MediaBlock media={s.media} />}
      </div>
    );
  return s.cases.length ? (
    <div className="case-grid">
      {s.cases.map((c) => (
        <SuccessCaseCard key={c.id} item={c} />
      ))}
    </div>
  ) : (
    <div className="case-empty">
      <h3>{site.labels.noCase}</h3>
      <p>{site.labels.noCaseDescription}</p>
      <ContactButton label={s.cta} location={`${s.slug}:cases`} />
    </div>
  );
}
