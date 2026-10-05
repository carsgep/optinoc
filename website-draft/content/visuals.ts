export type SolutionVisual = {
  headline: string;
  src: string;
  mobileSrc: string;
  alt: string;
  position: string;
};
const visual = (
  slug: string,
  headline: string,
  alt: string,
  position = "65% center",
): SolutionVisual => ({
  headline,
  src: `/media/solutions/${slug}/hero-v3.webp`,
  mobileSrc: `/media/solutions/${slug}/hero-v3-mobile.webp`,
  alt,
  position,
});
export const solutionVisuals: Record<string, SolutionVisual> = {
  "protect-recover": visual(
    "protect-recover",
    "Que un ataque no detenga tu negocio.",
    "Visual conceptual de una bóveda de datos protegida; imagen generada, no instalación de un cliente.",
  ),
  cloud: visual(
    "cloud",
    "Una nube a la altura de tu próximo paso.",
    "Visual conceptual de infraestructura cloud conectada entre nubes; imagen generada.",
  ),
  optinoc: visual(
    "optinoc",
    "De la alerta a la acción. Con contexto.",
    "Visual conceptual de un centro de observabilidad; no representa la interfaz real de OptiNOC.",
  ),
  infrastructure: visual(
    "infrastructure",
    "Una base sólida para un negocio que no se detiene.",
    "Visual conceptual de infraestructura empresarial y racks de servidores; imagen generada.",
  ),
  itsm: visual(
    "itsm",
    "Menos fricción. Más control de tu operación.",
    "Visual conceptual de procesos y servicios tecnológicos conectados; imagen generada.",
  ),
  "managed-services": visual(
    "managed-services",
    "Tecnología crítica. Un equipo que responde.",
    "Escena ilustrativa de especialistas en operación tecnológica; personas e instalación generadas.",
  ),
};
export const carouselContent = {
  intervalMs: 10000,
  read: "Conoce cómo lo resolvemos",
  hint: "Selecciona una solución para detener el recorrido y explorar.",
  imageNote: "Visual conceptual",
  storyTitle: "Del reto a una solución concreta.",
};
