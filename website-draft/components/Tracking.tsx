"use client";
import { useEffect, useRef } from "react";
import { track } from "@/lib/analytics";
export function CaseObserver({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          track("success_case_view", { id });
          observer.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [id]);
  return <div ref={ref}>{children}</div>;
}
