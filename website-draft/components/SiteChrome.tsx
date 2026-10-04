"use client";
import { useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { site } from "@/content/site";
import { solutions } from "@/content/solutions";
import { track } from "@/lib/analytics";
export function ContactButton({
  label = site.labels.ctaButton,
  location = "contact",
  secondary = false,
}: {
  label?: string;
  location?: string;
  secondary?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <button
        className={`button ${secondary ? "secondary" : "primary"}`}
        onClick={() => {
          track("cta_click", { location, label });
          dialog.current?.showModal();
        }}
      >
        {label}
      </button>
      <dialog
        ref={dialog}
        className="contact-dialog"
        aria-label={site.labels.contactDialogTitle}
        onClick={(e) => {
          if (e.target === e.currentTarget) dialog.current?.close();
        }}
      >
        <p className="eyebrow">{site.labels.draft}</p>
        <h2>{site.labels.contactDialogTitle}</h2>
        <p>{site.labels.contactDialogDescription}</p>
        <button
          className="button primary"
          onClick={() => dialog.current?.close()}
        >
          {site.labels.contactClose}
        </button>
      </dialog>
    </>
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
      <div className="draft-label">{site.labels.draft}</div>
    </>
  );
}
export function CTASection() {
  return (
    <section id="contacto" className="cta-section shell">
      <p className="eyebrow">{site.name}</p>
      <h2>{site.labels.ctaTitle}</h2>
      <p>{site.labels.ctaDescription}</p>
      <ContactButton />
      <small>{site.labels.contactDraft}</small>
    </section>
  );
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
          {solutions.map((s) => (
            <Link key={s.slug} href={`/soluciones/${s.slug}/`}>
              {s.name}
            </Link>
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
        <span>{site.labels.draft}</span>
      </div>
    </footer>
  );
}
