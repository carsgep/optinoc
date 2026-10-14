import Image from "next/image";
import Link from "next/link";
import type { Landing } from "@/content/landings";
import { ServiceCards } from "./ServiceCards";
import { AdvisoryForm } from "./AdvisoryForm";
export function ServiceLanding({ service: s }: { service: Landing }) {
  const experience: Record<string, { title: string; body: string }> = {
    "protect-recover": {
      title: "Preparar la recuperación de millones de archivos.",
      body: "Después del colapso de un servidor de archivos y una recuperación prolongada desde cintas, Optimize IT implementó una solución IBM Storage Defender para mejorar los procesos de respaldo y recuperación del cliente.",
    },
    "managed-services": {
      title: "Especialistas para una nueva plataforma IBM Fusion HCI.",
      body: "Una entidad financiera necesitaba administrar su nueva plataforma de virtualización. Optimize IT aportó especialistas e incorporó OptiNOC al monitoreo de sus servicios.",
    },
    optinoc: {
      title: "Monitoreo integrado con administración especializada.",
      body: "En una entidad financiera con una nueva plataforma IBM Fusion HCI, Optimize IT combinó especialistas y OptiNOC para apoyar la operación de sus servicios.",
    },
    itsm: {
      title: "Administración y parametrización de Maximo IT.",
      body: "En una operación de mesa de servicio, Optimize IT aportó especialistas para administrar Maximo IT, parametrizar los flujos de procesos y mantener las funcionalidades de la plataforma.",
    },
    "backup-as-a-service": {
      title: "Veeam, ExaGrid y Wasabi en una solución administrada.",
      body: "Para un cliente que requería protección integral, implementamos Backup as a Service. Nuestro equipo supervisa diariamente los respaldos y atiende las restauraciones conforme a los SLA acordados.",
    },
  };
  return (
    <main id="contenido" className="service-landing">
      <section className="service-hero">
        <picture>
          <source media="(max-width: 700px)" srcSet={s.mobileSrc} />
          <Image src={s.heroSrc} alt={s.alt} fill sizes="100vw" priority />
        </picture>
        <div className="service-hero-shade" />
        <div className="shell service-hero-copy">
          <Link className="back-link" href="/home-v2/#servicios">
            ← Todas las soluciones
          </Link>
          <p className="eyebrow">
            {s.category} / {s.shortName}
          </p>
          <h1>{s.headline}</h1>
          <p>{s.description}</p>
          <div className="hero-actions">
            <a className="button primary" href="#contacto">
              Solicitar asesoría gratuita ↗
            </a>
            <a className="service-secondary-link" href="#alcance">
              Conocer el servicio ↓
            </a>
          </div>
        </div>
        <span className="service-image-note">Visual conceptual</span>
        <nav className="service-section-nav shell" aria-label="En esta página">
          <a href="#reto">Su necesidad</a>
          <a href="#alcance">Cómo lo ayudamos</a>
          <a href="#enfoque">Nuestro enfoque</a>
          <a href="#preguntas">Preguntas frecuentes</a>
        </nav>
      </section>
      <section id="reto" className="service-intro shell">
        <div>
          <p className="eyebrow">01 / SU NECESIDAD</p>
          <h2>
            {s.slug === "itsm"
              ? "Un mejor servicio comienza por entender el proceso."
              : s.slug === "optinoc"
                ? "Menos búsqueda. Más contexto para actuar."
                : s.slug === "cleanshield"
                  ? "Preparar la recuperación también es proteger."
                  : "Una solución que parte de su operación."}
          </h2>
        </div>
        <div>
          {s.intro.map((t) => (
            <p key={t}>{t}</p>
          ))}
          <p className="service-challenge">{s.challenge}</p>
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
              Tecnología, procesos y especialistas alineados con las necesidades
              de su organización.
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
      {experience[s.slug] && (
        <section className="service-experience shell">
          <p className="eyebrow">EXPERIENCIA APLICADA</p>
          <h2>{experience[s.slug].title}</h2>
          <p>{experience[s.slug].body}</p>
          <span>Casos de Optimize IT · Clientes no identificados</span>
        </section>
      )}
      <section className="service-path shell">
        <p className="eyebrow">CÓMO COMENZAMOS</p>
        <h2>Una ruta clara para su necesidad.</h2>
        <div className="service-path-grid">
          {[
            {
              title: "Conocemos su situación",
              text: "Revisamos qué necesita resolver y las plataformas de las que depende su operación.",
            },
            {
              title: "Definimos el alcance",
              text: "Acordamos la solución, las responsabilidades y los criterios de trabajo.",
            },
            {
              title: "Acompañamos la implementación",
              text: "Prestamos los servicios definidos y revisamos su funcionamiento con el equipo.",
            },
          ].map((c, i) => (
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
