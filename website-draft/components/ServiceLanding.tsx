import Image from "next/image";
import Link from "next/link";
import type { Landing } from "@/content/landings";
import { ServiceCards } from "./ServiceCards";
import { AdvisoryForm } from "./AdvisoryForm";
export function ServiceLanding({ service: s }: { service: Landing }) {
  return (
    <main id="contenido" className="service-landing service-v2">
      <section className="service-hero">
        <picture>
          <source media="(max-width: 700px)" srcSet={s.mobileSrc} />
          <Image src={s.heroSrc} alt={s.alt} fill sizes="100vw" priority />
        </picture>
        <div className="service-hero-shade" />
        <div className="shell service-hero-copy">
          <Link
            className="back-link"
            href={
              s.parentSlug
                ? "/soluciones/protect-recover/"
                : "/home-v2/#servicios"
            }
          >
            ← {s.parentSlug ? "Protect and Recover" : "Todas las soluciones"}
          </Link>
          <p className="eyebrow">
            {s.parentSlug ? "PROTECT AND RECOVER / " : ""}
            {s.category} / {s.shortName}
          </p>
          <h1>{s.headline}</h1>
          <p className="service-subtitle">{s.subtitle}</p>
          <div className="hero-actions">
            <a className="button primary" href="#contacto">
              {s.cta} ↗
            </a>
            <a
              className="service-secondary-link"
              href={
                s.slug === "protect-recover"
                  ? "#soluciones-proteccion"
                  : "#alcance"
              }
            >
              {s.secondaryCta} ↓
            </a>
          </div>
        </div>
        <span className="service-image-note">Visual conceptual</span>
        <nav className="service-section-nav shell" aria-label="En esta página">
          <a href="#reto">Su necesidad</a>
          <a href="#beneficios">Beneficios</a>
          <a href="#alcance">Nuestra propuesta</a>
          {s.slug === "protect-recover" && (
            <a href="#soluciones-proteccion">Soluciones de protección</a>
          )}
          <a href="#proceso">Cómo trabajamos</a>
          <a href="#preguntas">Preguntas frecuentes</a>
        </nav>
      </section>
      <section id="reto" className="service-intro shell">
        <div>
          <p className="eyebrow">01 / SU NECESIDAD</p>
          <h2>¿Cuándo necesita esta solución?</h2>
        </div>
        <div>
          {s.intro.map((t) => (
            <p key={t}>{t}</p>
          ))}
          <ul className="need-list">
            {s.challenges.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      </section>
      <section id="beneficios" className="service-benefits shell">
        <p className="eyebrow">EL RESULTADO QUE BUSCAMOS</p>
        <h2>¿Qué puede obtener su organización?</h2>
        <div className="benefit-grid">
          {s.benefits.map((t, i) => (
            <article key={t}>
              <span aria-hidden="true">0{i + 1}</span>
              <p>{t}</p>
            </article>
          ))}
        </div>
      </section>
      <section id="alcance" className="service-scope">
        <div className="shell">
          <div className="section-heading">
            <div>
              <p className="eyebrow">02 / EL SERVICIO</p>
              <h2>{s.capabilityTitle}</h2>
            </div>
            <p>
              Tecnología, procedimientos y especialistas según el alcance que
              necesita su organización.
            </p>
          </div>
          <div className="capability-grid">
            {s.capabilities.map((c, i) => (
              <article key={c.title} className="capability-card">
                <span className="capability-number">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3>{c.title}</h3>
                <p>{c.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      {s.slug === "protect-recover" && (
        <section
          id="soluciones-proteccion"
          className="protection-solutions shell"
        >
          <p className="eyebrow">DENTRO DE PROTECT AND RECOVER</p>
          <h2>Dos soluciones para fortalecer su protección.</h2>
          <p>
            Contrate la solución de respaldo como servicio o añada análisis y
            validación de recuperación en un entorno aislado.
          </p>
          <ServiceCards slugs={["backup-as-a-service", "cleanshield"]} />
        </section>
      )}
      <section id="enfoque" className="service-approach shell">
        <div className="approach-image">
          <Image
            src={s.heroSrc}
            alt={s.alt}
            fill
            sizes="(max-width: 800px) 100vw, 45vw"
          />
          <div className="approach-caption">
            <span>OPTIMIZE IT</span>
            <strong>
              La tecnología necesita
              <br />
              una operación preparada.
            </strong>
          </div>
        </div>
        <div className="approach-copy">
          <p className="eyebrow">03 / NUESTRO ENFOQUE</p>
          {s.sections.map((g) => (
            <div key={g.title}>
              <h3>{g.title}</h3>
              {g.paragraphs.map((t) => (
                <p key={t}>{t}</p>
              ))}
            </div>
          ))}
          <div
            className="technology-pills"
            aria-label="Tecnologías y capacidades relacionadas"
          >
            {s.technologies.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </div>
      </section>
      {s.slug === "optinoc" && (
        <section className="product-preview shell">
          <div>
            <p className="eyebrow">LA PLATAFORMA</p>
            <h2>Información para orientar la atención.</h2>
            <p>
              Vista del producto OptiNOC. Las integraciones, consultas y rutas
              de escalamiento se definen para cada implementación.
            </p>
          </div>
          <Image
            src="/media/solutions/optinoc/dashboard.webp"
            alt="Captura de la plataforma OptiNOC"
            width={1440}
            height={900}
            sizes="100vw"
          />
        </section>
      )}
      <section id="proceso" className="service-path shell">
        <p className="eyebrow">CÓMO TRABAJAMOS</p>
        <h2>Una ruta clara para su necesidad.</h2>
        <div className="service-path-grid">
          {s.process.map((c, i) => (
            <div key={c.title}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              <h3>{c.title}</h3>
              <p>{c.text}</p>
            </div>
          ))}
        </div>
      </section>
      <section id="preguntas" className="service-faq shell">
        <div>
          <p className="eyebrow">04 / RESOLVEMOS SUS DUDAS</p>
          <h2>Preguntas frecuentes.</h2>
          <p>{s.closing}</p>
          <a href="#contacto" className="button primary">
            {s.cta} ↗
          </a>
        </div>
        <div>
          {s.faqs.map((f) => (
            <details key={f.question}>
              <summary>
                {f.question}
                <span aria-hidden="true">+</span>
              </summary>
              <p>{f.answer}</p>
            </details>
          ))}
        </div>
      </section>
      <section className="related-services shell">
        <p className="eyebrow">SOLUCIONES QUE SE COMPLEMENTAN</p>
        <h2>Conecte las piezas de su operación.</h2>
        <ServiceCards slugs={s.related} />
      </section>
      <AdvisoryForm key={s.slug} service={s.slug} />
    </main>
  );
}
