export type EventName =
  | "solution_view"
  | "solution_select"
  | "solution_section_view"
  | "carousel_pause"
  | "carousel_resume"
  | "cta_click"
  | "success_case_view";
type Payload = Record<string, string | number>;
let adapter: ((name: EventName, payload: Payload) => void) | undefined;
export function setAnalyticsAdapter(next: typeof adapter) {
  adapter = next;
}
export function track(name: EventName, payload: Payload = {}) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent("optimizeit:analytics", { detail: { name, ...payload } }),
  );
  adapter?.(name, payload);
}
