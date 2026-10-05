"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { solutions } from "@/content/solutions";
import { site } from "@/content/site";
import { solutionVisuals, carouselContent } from "@/content/visuals";
import { track } from "@/lib/analytics";
import { SolutionStory } from "./Story";
import { ContactButton } from "./SiteChrome";

export function SolutionsExperience() {
  const [index, setIndex] = useState(0),
    [step, setStep] = useState(0),
    [manual, setManual] = useState(false),
    [elapsed, setElapsed] = useState(0),
    [hover, setHover] = useState(false),
    [focus, setFocus] = useState(false),
    [visible, setVisible] = useState(true),
    [reduced, setReduced] = useState(true);
  const selectors = useRef<(HTMLButtonElement | null)[]>([]),
    steps = useRef<(HTMLButtonElement | null)[]>([]),
    touch = useRef<{ x: number; y: number } | null>(null),
    elapsedRef = useRef(0);
  const active = solutions[index],
    visual = solutionVisuals[active.slug];
  const running = !manual && !hover && !focus && visible && !reduced;
  const interval = carouselContent.intervalMs;
  useEffect(() => {
    const query = matchMedia("(prefers-reduced-motion: reduce)");
    const motion = () => setReduced(query.matches);
    const visibility = () => setVisible(!document.hidden);
    motion();
    visibility();
    query.addEventListener("change", motion);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      query.removeEventListener("change", motion);
      document.removeEventListener("visibilitychange", visibility);
    };
  }, []);
  useEffect(() => {
    if (!running) return;
    let previous = performance.now();
    const id = setInterval(() => {
      const now = performance.now();
      elapsedRef.current += now - previous;
      previous = now;
      if (elapsedRef.current >= interval) {
        setIndex((i) => (i + 1) % solutions.length);
        setStep(0);
        elapsedRef.current = 0;
      }
      setElapsed(elapsedRef.current);
    }, 100);
    return () => clearInterval(id);
  }, [running, interval]);
  useEffect(() => {
    track("solution_view", { slug: active.slug });
    if (manual || reduced) return;
    const next =
      solutionVisuals[solutions[(index + 1) % solutions.length].slug];
    const timer = setTimeout(() => {
      const image = new window.Image();
      image.src = matchMedia("(max-width:760px)").matches
        ? next.mobileSrc
        : next.src;
    }, 500);
    return () => clearTimeout(timer);
  }, [active.slug, index, manual, reduced]);
  function reset() {
    elapsedRef.current = 0;
    setElapsed(0);
  }
  function stop(reason: string) {
    setManual(true);
    reset();
    track("carousel_pause", { reason });
  }
  function select(next: number, keyboard = false) {
    const n = (next + solutions.length) % solutions.length;
    stop("selection");
    setIndex(n);
    setStep(0);
    track("solution_select", { slug: solutions[n].slug });
    if (keyboard) selectors.current[n]?.focus();
  }
  function changeStep(next: number, keyboard = false) {
    const n = (next + site.labels.steps.length) % site.labels.steps.length;
    stop("story");
    setStep(n);
    track("solution_section_view", {
      slug: active.slug,
      section: site.labels.steps[n],
    });
    if (keyboard) steps.current[n]?.focus();
  }
  function touchStart(e: React.TouchEvent) {
    touch.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  }
  function touchEnd(e: React.TouchEvent) {
    if (!touch.current) return;
    const dx = e.changedTouches[0].clientX - touch.current.x,
      dy = e.changedTouches[0].clientY - touch.current.y;
    if (Math.abs(dx) > 65 && Math.abs(dx) > Math.abs(dy) * 1.5)
      select(index + (dx < 0 ? 1 : -1));
    touch.current = null;
  }
  function toggle() {
    if (manual) {
      setManual(false);
      reset();
      track("carousel_resume");
    } else stop("button");
  }
  return (
    <section
      id="soluciones"
      className="visual-experience"
      aria-label={site.labels.portfolio}
    >
      <div
        className="visual-hero"
        onTouchStart={touchStart}
        onTouchEnd={touchEnd}
        onClick={(e) => {
          if (!(e.target as HTMLElement).closest("a,button"))
            stop("hero-reading");
        }}
      >
        <div
          id="solution-panel"
          role="tabpanel"
          aria-labelledby={"solution-" + active.slug}
          className="visual-slide"
        >
          <picture className="visual-picture" key={active.slug}>
            <source media="(max-width:760px)" srcSet={visual.mobileSrc} />
            <Image
              src={visual.src}
              alt={visual.alt}
              fill
              sizes="100vw"
              priority={index === 0}
              loading={index === 0 ? undefined : "eager"}
              className="visual-image"
              style={{ objectPosition: visual.position }}
            />
          </picture>
          <div className="visual-shade" aria-hidden="true" />
          <div
            className="visual-copy shell"
            onFocusCapture={() => setFocus(true)}
            onBlurCapture={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) setFocus(false);
            }}
          >
            <p className="visual-kicker">
              {String(index + 1).padStart(2, "0")} /{" "}
              {String(solutions.length).padStart(2, "0")}{" "}
              <span>{active.name}</span>
            </p>
            <h1 id="portfolio-title">{visual.headline}</h1>
            <p className="visual-description">{active.description}</p>
            <a
              className="button primary visual-read"
              href="#solution-story"
              onClick={() => stop("read")}
            >
              {carouselContent.read}
            </a>
          </div>
          <span className="visual-image-note">{carouselContent.imageNote}</span>
        </div>
        <div className="visual-deck shell">
          <div className="visual-control-row">
            <span className="visual-hint">{carouselContent.hint}</span>
            <div className="arrow-controls">
              <button
                aria-label={site.labels.previous}
                onClick={() => select(index - 1)}
              >
                ←
              </button>
              <button
                aria-label={site.labels.next}
                onClick={() => select(index + 1)}
              >
                →
              </button>
            </div>
          </div>
          <div
            className="solution-selector"
            role="tablist"
            aria-label={site.labels.portfolio}
            onFocusCapture={() => setFocus(true)}
            onBlurCapture={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) setFocus(false);
            }}
          >
            {solutions.map((s, i) => (
              <button
                key={s.slug}
                ref={(e) => {
                  selectors.current[i] = e;
                }}
                role="tab"
                id={"solution-" + s.slug}
                aria-controls="solution-panel"
                aria-selected={index === i}
                tabIndex={index === i ? 0 : -1}
                onClick={() => select(i)}
                onKeyDown={(e) => {
                  const next =
                    e.key === "ArrowRight"
                      ? index + 1
                      : e.key === "ArrowLeft"
                        ? index - 1
                        : e.key === "Home"
                          ? 0
                          : e.key === "End"
                            ? solutions.length - 1
                            : null;
                  if (next !== null) {
                    e.preventDefault();
                    select(next, true);
                  }
                }}
              >
                <span>{String(i + 1).padStart(2, "0")}</span>
                {s.shortName}
              </button>
            ))}
          </div>
          <div className="timer-controls">
            <span>
              {reduced || manual
                ? site.labels.manual
                : running
                  ? site.labels.automatic
                  : site.labels.temporary}
            </span>
            <div
              className="timer"
              role="progressbar"
              aria-label={site.labels.progress}
              aria-valuemin={0}
              aria-valuemax={interval / 1000}
              aria-valuenow={Math.min(
                interval / 1000,
                Math.floor(elapsed / 1000),
              )}
            >
              <span
                style={{
                  width: Math.min(100, (elapsed / interval) * 100) + "%",
                }}
              />
            </div>
            <button disabled={reduced} onClick={toggle}>
              {manual || reduced ? site.labels.resume : site.labels.pause}
            </button>
          </div>
        </div>
      </div>
      <div id="solution-story" className="story-shell shell" tabIndex={-1}>
        <div
          className="solution-frame"
          onClickCapture={() => {
            if (!manual) stop("story-reading");
          }}
          onPointerEnter={(e) => {
            if (e.pointerType === "mouse") setHover(true);
          }}
          onPointerLeave={() => setHover(false)}
          onFocusCapture={() => setFocus(true)}
          onBlurCapture={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) setFocus(false);
          }}
          onTouchStart={touchStart}
          onTouchEnd={touchEnd}
        >
          <div className="solution-top">
            <div>
              <p className="eyebrow">{carouselContent.storyTitle}</p>
              <h2>{active.name}</h2>
              <p>{active.description}</p>
            </div>
          </div>
          <div
            className="story-navigation"
            role="tablist"
            aria-label={active.name}
          >
            {site.labels.steps.map((label, i) => (
              <button
                key={label}
                ref={(e) => {
                  steps.current[i] = e;
                }}
                role="tab"
                id={"story-tab-" + i}
                aria-controls={"story-panel-" + i}
                aria-selected={step === i}
                tabIndex={step === i ? 0 : -1}
                onClick={() => changeStep(i)}
                onKeyDown={(e) => {
                  const next =
                    e.key === "ArrowRight"
                      ? step + 1
                      : e.key === "ArrowLeft"
                        ? step - 1
                        : e.key === "Home"
                          ? 0
                          : e.key === "End"
                            ? site.labels.steps.length - 1
                            : null;
                  if (next !== null) {
                    e.preventDefault();
                    changeStep(next, true);
                  }
                }}
              >
                <span>{String(i + 1).padStart(2, "0")}</span>
                {label}
              </button>
            ))}
          </div>
          {site.labels.steps.map((label, i) => (
            <div
              key={label}
              role="tabpanel"
              id={"story-panel-" + i}
              aria-labelledby={"story-tab-" + i}
              tabIndex={0}
              hidden={step !== i}
              className="story-panel"
            >
              {step === i && <SolutionStory solution={active} step={i} />}
            </div>
          ))}
          <div className="solution-actions">
            <ContactButton label={active.cta} location={active.slug} />
            <Link href={"/soluciones/" + active.slug + "/"}>
              {site.labels.detail}
            </Link>
            {active.secondaryCta && (
              <a href={active.secondaryCta.href}>{active.secondaryCta.label}</a>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
