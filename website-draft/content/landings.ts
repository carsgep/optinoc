import copy from "./landing-copy.json";
import { solutionVisuals } from "./visuals";
export const landingExtras: Record<
  string,
  {
    category: string;
    shortName: string;
    image: string;
    related: string[];
    technologies: string[];
  }
> = {
  "protect-recover": {
    category: "PROTECCIÓN DE DATOS",
    shortName: "Protect & Recover",
    image: "protect-recover",
    related: ["backup-as-a-service", "cleanshield"],
    technologies: [
      "IBM Storage Defender Data Protect",
      "Veeam Backup & Replication",
      "IBM Storage Protect",
      "Predatar",
      "IBM Safeguarded Copy",
      "IBM Storage Defender Sentinel",
    ],
  },
  cloud: {
    category: "CLOUD EMPRESARIAL",
    shortName: "Cloud",
    image: "cloud",
    related: ["managed-services", "protect-recover"],
    technologies: ["AWS", "Microsoft Azure", "IBM Cloud"],
  },
  infrastructure: {
    category: "INFRAESTRUCTURA EMPRESARIAL",
    shortName: "Infrastructure",
    image: "infrastructure",
    related: ["managed-services", "protect-recover"],
    technologies: [
      "IBM Power",
      "IBM Storage FlashSystem",
      "IBM Storage Scale",
      "IBM Spectrum Control",
      "Dell",
      "HPE",
      "Lenovo",
    ],
  },
  "managed-services": {
    category: "OPERACIÓN ESPECIALIZADA",
    shortName: "Managed Services",
    image: "managed-services",
    related: ["optinoc", "backup-as-a-service"],
    technologies: [
      "AIX",
      "Linux",
      "Windows",
      "Oracle Database",
      "Red Hat OpenShift",
      "IBM Fusion HCI",
      "AWS",
      "Microsoft Azure",
      "IBM Cloud",
    ],
  },
  itsm: {
    category: "PROCESOS Y SERVICIOS",
    shortName: "ITSM",
    image: "itsm",
    related: ["optidesk", "managed-services"],
    technologies: ["ITIL", "IBM Maximo IT", "GLPI"],
  },
  optinoc: {
    category: "IA PROPIETARIA DE OPTIMIZE IT",
    shortName: "OptiNOC",
    image: "optinoc",
    related: ["managed-services", "itsm"],
    technologies: ["Nagios", "IBM Instana", "OPTI · Asistente de OptiNOC"],
  },
  optidesk: {
    category: "IA PROPIETARIA DE OPTIMIZE IT",
    shortName: "Optidesk",
    image: "optidesk",
    related: ["itsm", "optinoc"],
    technologies: [
      "IA generativa",
      "Integración con ITSM",
      "Conocimiento de soporte",
    ],
  },
  "backup-as-a-service": {
    category: "RESPALDO COMO SERVICIO",
    shortName: "Backup as a Service",
    image: "backup-as-a-service",
    related: ["protect-recover", "cleanshield"],
    technologies: ["Veeam Backup & Replication", "ExaGrid", "Wasabi"],
  },
  cleanshield: {
    category: "RECUPERACIÓN AISLADA",
    shortName: "CleanShield",
    image: "cleanshield",
    related: ["protect-recover", "backup-as-a-service"],
    technologies: [
      "Predatar",
      "Veeam Backup & Replication",
      "IBM Storage Protect",
      "IBM Storage Defender Data Protect",
    ],
  },
};
export const landings = copy.map((item) => {
  const extra = landingExtras[item.slug];
  const visual = solutionVisuals[item.slug];
  return {
    ...item,
    ...extra,
    parentSlug: ["backup-as-a-service", "cleanshield"].includes(item.slug)
      ? "protect-recover"
      : undefined,
    heroSrc:
      item.slug === "cleanshield"
        ? "/media/solutions/cleanshield/hero-v4.webp"
        : (visual?.src ?? `/media/solutions/${extra.image}/hero-v3.webp`),
    mobileSrc:
      (item.slug === "cleanshield"
        ? "/media/solutions/cleanshield/hero-v4-mobile.webp"
        : visual?.mobileSrc) ??
      `/media/solutions/${extra.image}/hero-v3-mobile.webp`,
    alt:
      visual?.alt ??
      `Visual conceptual de ${extra.shortName}; imagen generada.`,
  };
});
export type Landing = (typeof landings)[number];
export function getLanding(slug: string) {
  return landings.find((item) => item.slug === slug);
}

export const primaryLandings = landings.filter((s) => !s.parentSlug);
