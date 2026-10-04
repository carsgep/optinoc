"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { solutions } from "@/content/solutions";
import { site } from "@/content/site";
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
  const active = solutions[index];
  const running = !manual && !hover && !focus && visible && !reduced;
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
      if (elapsedRef.current >= 15000) {
        setIndex((i) => (i + 1) % solutions.length);
        setStep(0);
        elapsedRef.current = 0;
      }
      setElapsed(elapsedRef.current);
    }, 100);
    return () => clearInterval(id);
  }, [running]);
  useEffect(() => {
    track("solution_view", { slug: active.slug });
  }, [active.slug]);
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
    const n = (next + 4) % 4;
    stop("story");
    setStep(n);
    track("solution_section_view", {
      slug: active.slug,
      section: site.labels.steps[n],
    });
    if (keyboard) steps.current[n]?.focus();
  }
  return (
    <section
      id="soluciones"
      className="portfolio shell"
      aria-labelledby="portfolio-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">{site.labels.portfolio}</p>
          <h2 id="portfolio-title">{site.labels.portfolioTitle}</h2>
        </div>
        <p>{site.labels.portfolioDescription}</p>
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
            id={`solution-${s.slug}`}
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
      <div
        className="solution-frame"
        role="tabpanel"
        id="solution-panel"
        aria-labelledby={`solution-${active.slug}`}
        onPointerEnter={(e) => {
          if (e.pointerType === "mouse") setHover(true);
        }}
        onPointerLeave={() => setHover(false)}
        onFocusCapture={() => setFocus(true)}
        onBlurCapture={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget)) setFocus(false);
        }}
        onTouchStart={(e) => {
          touch.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        }}
        onTouchEnd={(e) => {
          if (!touch.current) return;
          const dx = e.changedTouches[0].clientX - touch.current.x,
            dy = e.changedTouches[0].clientY - touch.current.y;
          if (Math.abs(dx) > 65 && Math.abs(dx) > Math.abs(dy) * 1.5)
            select(index + (dx < 0 ? 1 : -1));
          touch.current = null;
        }}
      >
        <div className="solution-top">
          <div>
            <p className="eyebrow">
              {String(index + 1).padStart(2, "0")} /{" "}
              {String(solutions.length).padStart(2, "0")}
            </p>
            <h3>{active.name}</h3>
            <p>{active.description}</p>
          </div>
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
              id={`story-tab-${i}`}
              aria-controls={`story-panel-${i}`}
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
                          ? 3
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
            id={`story-panel-${i}`}
            aria-labelledby={`story-tab-${i}`}
            tabIndex={0}
            hidden={step !== i}
            className="story-panel"
          >
            {step === i && <SolutionStory solution={active} step={i} />}
          </div>
        ))}
        <div className="solution-actions">
          <ContactButton label={active.cta} location={active.slug} />
          <Link href={`/soluciones/${active.slug}/`}>{site.labels.detail}</Link>
          {active.secondaryCta && (
            <a href={active.secondaryCta.href}>{active.secondaryCta.label}</a>
          )}
        </div>
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
          aria-valuemax={15}
          aria-valuenow={Math.min(15, Math.floor(elapsed / 1000))}
        >
          <span style={{ width: `${Math.min(100, elapsed / 150)}%` }} />
        </div>
        <button
          disabled={reduced}
          onClick={() => {
            if (manual) {
              setManual(false);
              reset();
              track("carousel_resume");
            } else stop("button");
          }}
        >
          {manual || reduced ? site.labels.resume : site.labels.pause}
        </button>
      </div>
    </section>
  );
}
