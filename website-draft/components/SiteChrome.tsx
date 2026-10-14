"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { site } from "@/content/site";
import { landings, primaryLandings } from "@/content/landings";
import { AdvisoryForm } from "./AdvisoryForm";
import { track } from "@/lib/analytics";
export function ContactButton({
  label = "Solicitar asesoría gratuita",
  location = "contact",
  secondary = false,
}: {
  label?: string;
  location?: string;
  secondary?: boolean;
}) {
  return (
    <a
      href="#contacto"
      className={`button ${secondary ? "secondary" : "primary"}`}
      onClick={() => track("cta_click", { location, label })}
    >
      {label}
    </a>
  );
}
export function Navigation() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <a className="skip" href="#contenido">
        {site.labels.skip}
      </a>
      <header className="navigation">
        <div className="nav-inner">
          <Link
            href="/home-v2/"
            aria-label={`${site.name} · ${site.labels.home}`}
          >
            <Image
              className="logo"
              src={site.logo.src}
              alt={site.logo.alt}
              width={600}
              height={157}
              priority
            />
          </Link>
          <button
            className="menu-toggle"
            aria-expanded={open}
            aria-controls="main-nav"
            onClick={() => setOpen(!open)}
          >
            {open ? site.labels.close : site.labels.menu}
          </button>
          <nav
            id="main-nav"
            className={open ? "open" : ""}
            aria-label="Principal"
            onKeyDown={(e) => {
              if (e.key === "Escape") setOpen(false);
            }}
          >
            <details className="solutions-dropdown">
              <summary>Servicios ▾</summary>
              <div>
                {primaryLandings.map((s) => (
                  <div className="nav-service-group" key={s.slug}>
                    <Link
                      href={`/soluciones/${s.slug}/`}
                      onClick={(e) => {
                        setOpen(false);
                        e.currentTarget
                          .closest("details")
                          ?.removeAttribute("open");
                      }}
                    >
                      {s.shortName}
                    </Link>
                    {landings
                      .filter((child) => child.parentSlug === s.slug)
                      .map((child) => (
                        <Link
                          className="nav-child-solution"
                          key={child.slug}
                          href={`/soluciones/${child.slug}/`}
                          onClick={(e) => {
                            setOpen(false);
                            e.currentTarget
                              .closest("details")
                              ?.removeAttribute("open");
                          }}
                        >
                          {child.shortName}
                        </Link>
                      ))}
                  </div>
                ))}
              </div>
            </details>
            {site.nav.map((n) => (
              <Link key={n.href} href={n.href} onClick={() => setOpen(false)}>
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="nav-contact">
            <ContactButton
              label={site.hero.secondary}
              location="header"
              secondary
            />
          </div>
        </div>
      </header>
      {site.draft && <div className="draft-label">{site.labels.draft}</div>}
    </>
  );
}
export function CTASection() {
  return <AdvisoryForm />;
}
export function Footer() {
  return (
    <footer className="footer shell">
      <div className="footer-grid">
        <div>
          <Image
            className="logo"
            src={site.logo.src}
            alt={site.logo.alt}
            width={600}
            height={157}
          />
          <p>{site.labels.footerTagline}</p>
        </div>
        <nav aria-label="Soluciones en el pie de página">
          {primaryLandings.map((s) => (
            <div className="footer-service-group" key={s.slug}>
              <Link href={`/soluciones/${s.slug}/`}>{s.shortName}</Link>
              {landings
                .filter((child) => child.parentSlug === s.slug)
                .map((child) => (
                  <Link
                    className="footer-child-solution"
                    key={child.slug}
                    href={`/soluciones/${child.slug}/`}
                  >
                    {child.shortName}
                  </Link>
                ))}
            </div>
          ))}
        </nav>
        <div>
          <a href="#contacto">{site.labels.contact}</a>
          <a href={site.privacyUrl} target="_blank" rel="noopener noreferrer">
            {site.labels.privacy}
          </a>
          {site.social.map((s) => (
            <a
              key={s.href}
              href={s.href}
              target="_blank"
              rel="noopener noreferrer"
            >
              {s.label}
            </a>
          ))}
        </div>
      </div>
      <div className="footer-bottom">
        <span>{site.legal}</span>
        {site.draft && <span>{site.labels.draft}</span>}
      </div>
    </footer>
  );
}
