import Image from "next/image";
import Link from "next/link";
import { landings } from "@/content/landings";
export function ServiceCards({ slugs }: { slugs?: string[] }) {
  const items = slugs
    ? slugs
        .map((slug) => landings.find((s) => s.slug === slug))
        .filter((s) => !!s)
    : landings;
  return (
    <div className="service-card-grid">
      {items.map((s) => (
        <Link
          className="service-card"
          href={`/soluciones/${s.slug}/`}
          key={s.slug}
        >
          <div className="service-card-image">
            <Image
              src={s.heroSrc}
              alt={s.alt}
              fill
              sizes="(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw"
            />
            <span aria-hidden="true">↗</span>
          </div>
          <div className="service-card-copy">
            <p className="eyebrow">{s.category}</p>
            <h3>{s.shortName}</h3>
            <p>{s.description}</p>
            <span className="card-link">
              Explorar la solución <span aria-hidden="true">→</span>
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
