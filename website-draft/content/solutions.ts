import { getLanding } from "./landings";
export type Media = {
  type: "image" | "video";
  src: string;
  alt: string;
  poster?: string;
  caption?: string;
};
export type Evidence = {
  value: string;
  label: string;
  context: string;
  source: string;
  sourceUrl: string;
  publicationYear: number;
};
export type Metric = { value: string; label: string; context?: string };
export type SuccessCase = {
  id: string;
  sector: string;
  title: string;
  challenge: string;
  solution: string;
  result: string;
  technologies: string[];
  clientName?: string;
  logo?: Media;
  requiresValidation?: boolean;
};
export type Solution = {
  slug: string;
  name: string;
  shortName: string;
  tagline: string;
  description: string;
  problem: string;
  proposal: string;
  evidence: Evidence[];
  capabilities: { title: string; description: string }[];
  metrics: Metric[];
  experience: string;
  cases: SuccessCase[];
  technologies: string[];
  media?: Media;
  cta: string;
  secondaryCta?: { label: string; href: string };
  references: { label: string; url: string }[];
  claims?: { text: string; requiresValidation: boolean }[];
};

const uptimeUrl =
  "https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2025.AnnualSurvey.OutagesAI.3Pager.pdf?version=0";
const newRelicUrl = "https://newrelic.com/press-release/20250917";
const flexeraUrl = "https://info.flexera.com/CM-REPORT-State-of-the-Cloud-AWS";
const processEvidence: Evidence = {
  value: "87 %",
  label: "consideró prevenible su última interrupción importante",
  context:
    "98 encuestados que experimentaron una interrupción significativa, seria o severa; percepción sobre mejores procesos o gestión.",
  source: "Uptime Institute",
  sourceUrl: uptimeUrl,
  publicationYear: 2025,
};
const outageEvidence: Evidence = {
  value: "57 %",
  label: "reportó costos de al menos US$100.000",
  context:
    "94 respuestas sobre su interrupción más relevante de categorías 3–5. Incluye costos directos, oportunidad y reputación.",
  source: "Uptime Institute",
  sourceUrl: uptimeUrl,
  publicationYear: 2025,
};
const engineeringEvidence: Evidence = {
  value: "33 %",
  label: "del tiempo de ingeniería se dedica a interrupciones",
  context:
    "Estudio de 1.700 profesionales y líderes de TI e ingeniería, 23 países; no representa resultados de Optimize IT.",
  source: "New Relic / ETR",
  sourceUrl: newRelicUrl,
  publicationYear: 2025,
};

export const cases: SuccessCase[] = [
  {
    id: "recovery",
    sector: "Organizaciones empresariales",
    title: "Recuperar la información después del ransomware",
    challenge: "Recuperar información afectada por ataques de ransomware.",
    solution: "Acompañamiento especializado de Optimize IT en la recuperación.",
    result:
      "Dos organizaciones recuperaron su información con nuestro apoyo. No se han documentado aquí tiempos ni porcentajes de recuperación.",
    technologies: [],
  },
  {
    id: "fusion",
    sector: "Sector financiero colombiano",
    title: "Operación especializada de una plataforma de virtualización",
    challenge:
      "Administrar la plataforma de virtualización de una importante entidad financiera.",
    solution: "Administración de IBM Fusion por el equipo de Optimize IT.",
    result:
      "Plataforma bajo administración especializada. Indicadores del caso pendientes de documentación.",
    technologies: ["IBM Fusion"],
  },
  {
    id: "defender",
    sector: "Sector financiero colombiano",
    title: "Una arquitectura orientada a la ciberresiliencia",
    challenge:
      "Fortalecer la protección de información de una entidad financiera.",
    solution: "Implementación de IBM Storage Defender.",
    result:
      "Implementación reportada por Optimize IT. El alcance y sus indicadores deben validarse antes del lanzamiento.",
    technologies: ["IBM Storage Defender"],
    requiresValidation: true,
  },
];

const originalSolutions: Solution[] = [
  {
    slug: "protect-recover",
    name: "Optimize Protect & Recover",
    shortName: "Protect & Recover",
    tagline: "La tranquilidad no está en copiar. Está en poder recuperar.",
    description:
      "Protección de información y ciberresiliencia diseñadas alrededor de la continuidad de tu negocio.",
    problem:
      "Un backup solo tiene valor si puedes recuperarlo cuando el negocio lo necesita. Ransomware, corrupción, errores humanos y fallas de infraestructura exigen copias protegidas y recuperaciones probadas, con objetivos de pérdida de datos (RPO) y tiempo de recuperación (RTO) definidos.",
    proposal:
      "Diseñamos la estrategia, implementamos la arquitectura y operamos la protección de tus datos. Conectamos políticas de retención, inmutabilidad y pruebas de recuperación en entornos on-premise, cloud e híbridos.",
    evidence: [
      outageEvidence,
      {
        value: "US$4,44 M",
        label: "costo promedio global de una brecha de datos",
        context:
          "IBM Cost of a Data Breach 2025. Promedio de brechas estudiadas; no es el costo de todo incidente ni una estimación para tu empresa.",
        source: "IBM",
        sourceUrl:
          "https://newsroom.ibm.com/2025-07-30-ibm-report-13-of-organizations-reported-breaches-of-ai-models-or-applications%2C-97-of-which-reported-lacking-proper-ai-access-controls",
        publicationYear: 2025,
      },
    ],
    capabilities: [
      {
        title: "Estrategia y evaluación",
        description:
          "Riesgo, retención, RPO y RTO traducidos en una política de protección costo-eficiente.",
      },
      {
        title: "Arquitectura de protección",
        description:
          "Diseño e implementación de respaldos para infraestructura local, nube y entornos híbridos.",
      },
      {
        title: "Ciberresiliencia",
        description:
          "Inmutabilidad, análisis de respaldos y validación para preparar recuperaciones limpias.",
      },
      {
        title: "Disaster & Cyber Recovery",
        description:
          "Planes y pruebas de recuperación que ponen a prueba la continuidad antes de un incidente.",
      },
      {
        title: "Backup as a Service",
        description:
          "Protección con Veeam bajo mensualidad: infraestructura, licencias, plataforma, operación, monitoreo y servicios profesionales.",
      },
    ],
    metrics: [
      { value: "+7 PB", label: "de información protegida" },
      { value: "+50.000", label: "respaldos administrados al mes" },
      { value: "99,96 %", label: "éxito en respaldos" },
      { value: "2", label: "organizaciones recuperadas tras ransomware" },
    ],
    experience:
      "Más de 15 años protegiendo información, incluyendo instituciones financieras. Experiencia con IBM Storage Defender y Predatar para fortalecer la ciberresiliencia.",
    cases: [cases[0], cases[2]],
    technologies: [
      "IBM",
      "Veeam",
      "Dell",
      "Lenovo",
      "AWS",
      "Microsoft Azure",
      "Wasabi",
      "Predatar",
    ],
    cta: "Evalúa tu estrategia de recuperación",
    references: [
      {
        label: "CISA · Guía de prevención y recuperación ante ransomware",
        url: "https://www.cisa.gov/stopransomware/ransomware-guide",
      },
    ],
    claims: [
      {
        text: "Primera implementación de IBM Storage Defender en Colombia",
        requiresValidation: true,
      },
      {
        text: "Implementación pionera de Predatar en Colombia",
        requiresValidation: true,
      },
    ],
  },
  {
    slug: "cloud",
    name: "Optimize Cloud",
    shortName: "Cloud",
    tagline: "Una nube que responde al negocio. Y a su presupuesto.",
    description:
      "Arquitectura, migración y operación cloud con automatización y gobierno desde el inicio.",
    problem:
      "Mover cargas a la nube no resuelve por sí solo la complejidad. Consumos sin control, aplicaciones legacy y procesos manuales pueden frenar la agilidad que el negocio espera.",
    proposal:
      "Definimos contigo qué mover, cómo diseñarlo y cómo operarlo. Combinamos arquitectura, automatización y gobierno de consumo para construir una nube preparada para evolucionar.",
    evidence: [
      {
        value: "84 %",
        label: "identifica gestionar el gasto como un reto cloud",
        context:
          "State of the Cloud 2025: 759 usuarios y responsables de nube encuestados a nivel mundial.",
        source: "Flexera",
        sourceUrl: flexeraUrl,
        publicationYear: 2025,
      },
      {
        value: "27 %",
        label: "del gasto cloud se estima desperdiciado",
        context:
          "Estimación de los encuestados en el informe 2025; no es un ahorro garantizado.",
        source: "Flexera",
        sourceUrl: flexeraUrl,
        publicationYear: 2025,
      },
    ],
    capabilities: [
      {
        title: "Assessment y arquitectura",
        description:
          "Priorización de cargas, resiliencia, seguridad y dimensionamiento.",
      },
      {
        title: "Migración",
        description:
          "Planificación y movimiento de aplicaciones a nube pública.",
      },
      {
        title: "IaC y DevOps",
        description:
          "Infraestructura reproducible y automatización con Terraform.",
      },
      {
        title: "Operación y soporte",
        description:
          "Administración de servicios y acompañamiento especializado.",
      },
      {
        title: "Gobierno y optimización",
        description:
          "Visibilidad del consumo y revisión continua del dimensionamiento.",
      },
    ],
    metrics: [
      { value: "+5 años", label: "implementando y administrando cargas cloud" },
      {
        value: "99,9 %",
        label: "disponibilidad en servicios cloud administrados",
      },
    ],
    experience:
      "Equipo profesional y certificado para acompañar la arquitectura, migración y administración de servicios cloud.",
    cases: [],
    technologies: ["AWS", "Microsoft Azure", "IBM Cloud", "Terraform"],
    cta: "Analicemos tu arquitectura Cloud",
    references: [
      { label: "Flexera · State of the Cloud 2025", url: flexeraUrl },
    ],
  },
  {
    slug: "optinoc",
    name: "OptiNOC",
    shortName: "OptiNOC",
    tagline: "De la alerta aislada a una decisión con contexto.",
    description:
      "Observabilidad atendida por IA, diagnóstico por capas y escalamiento operativo por voz.",
    problem:
      "Las alertas dispersas obligan al equipo a correlacionar señales manualmente. Sin contexto de servicio, diagnosticar y encontrar a la guardia correcta consume tiempo de respuesta.",
    proposal:
      "OptiNOC conecta el monitoreo con el inventario, las dependencias y diagnósticos especializados. OPTI consulta, explica y contacta por voz a la guardia definida, con evidencia y trazabilidad.",
    evidence: [engineeringEvidence, processEvidence],
    capabilities: [
      {
        title: "Observar y relacionar",
        description:
          "Conecta aplicaciones, contenedores, bases de datos y sistemas operativos con el servicio de negocio.",
      },
      {
        title: "Diagnosticar",
        description:
          "Reúne señales y ejecuta diagnósticos especializados de solo lectura por defecto.",
      },
      {
        title: "Conversar con OPTI",
        description:
          "Consultas en lenguaje natural y explicación de hallazgos operativos por voz.",
      },
      {
        title: "Escalar con contexto",
        description:
          "Aplica turnos, rutas y confirmaciones según políticas definidas.",
      },
    ],
    metrics: [],
    experience:
      "La plataforma integra mapa de servicios, diagnóstico de incidentes y un asistente de voz. El alcance de cada demostración se acuerda según el servicio y las tecnologías del cliente.",
    cases: [],
    technologies: ["OpenShift", "DB2", "Linux", "Aplicaciones web"],
    media: {
      type: "image",
      src: "/media/solutions/optinoc/dashboard.webp",
      alt: "Dashboard real de OptiNOC con estado de servicios y alertas",
      caption: "Vista de la plataforma OptiNOC",
    },
    cta: "Agenda una demo de OptiNOC",
    secondaryCta: {
      label: "Conoce OptiNOC",
      href: "https://www.optimizeit.co/optinoc2/",
    },
    references: [
      {
        label: "Optimize IT · Landing pública de OptiNOC",
        url: "https://www.optimizeit.co/optinoc2/",
      },
    ],
  },
  {
    slug: "infrastructure",
    name: "Optimize Infrastructure",
    shortName: "Infrastructure",
    tagline: "La infraestructura sobre la que corre tu negocio.",
    description:
      "Plataformas empresariales para cargas críticas, diseñadas con una visión de continuidad.",
    problem:
      "El crecimiento de los datos y las plataformas legacy exigen renovar capacidad sin perder continuidad. Cómputo, almacenamiento, conectividad y virtualización deben funcionar como una arquitectura coherente.",
    proposal:
      "Diseñamos e integramos plataformas para las necesidades reales de cada carga. De IBM Power y x86 al almacenamiento empresarial y la nube privada, conectamos capacidad, disponibilidad y operación.",
    evidence: [outageEvidence, processEvidence],
    capabilities: [
      {
        title: "Compute",
        description:
          "IBM Power y servidores x86 Dell y Lenovo para cargas empresariales.",
      },
      {
        title: "Storage",
        description:
          "Arquitecturas de almacenamiento empresarial con experiencia en IBM FlashSystem.",
      },
      {
        title: "Connectivity",
        description: "Conectividad LAN, SAN, Fibre Channel y switching.",
      },
      {
        title: "Virtualization & Private Cloud",
        description:
          "IBM Fusion, OpenShift y VMware en arquitecturas de virtualización e infraestructura híbrida.",
      },
    ],
    metrics: [{ value: "17 años", label: "trabajando con IBM" }],
    experience:
      "Experiencia integrando tecnología IBM y administrando IBM Fusion para una importante entidad del sector financiero colombiano.",
    cases: [cases[1]],
    technologies: [
      "IBM Power",
      "IBM FlashSystem",
      "IBM Fusion",
      "Red Hat OpenShift",
      "Dell",
      "Lenovo",
      "VMware",
    ],
    cta: "Diseñemos tu próxima plataforma",
    references: [
      { label: "Uptime Institute · Encuesta global 2025", url: uptimeUrl },
      {
        label: "IBM · Programa Partner Plus",
        url: "https://www.ibm.com/partnerplus/",
      },
    ],
    claims: [
      {
        text: "IBM Partner Plus Gold — nivel informado por Optimize IT; confirmar vigencia y permiso de uso del distintivo antes del lanzamiento.",
        requiresValidation: true,
      },
    ],
  },
  {
    slug: "itsm",
    name: "Optimize ITSM",
    shortName: "ITSM",
    tagline: "Procesos, tecnología y operación. En una misma dirección.",
    description:
      "Una gestión de servicios que conecta solicitudes, personas, activos y compromisos.",
    problem:
      "Solicitudes por múltiples canales, procesos manuales y activos desconectados dificultan la trazabilidad. Una herramienta necesita procesos claros, responsables y criterios de servicio para aportar valor.",
    proposal:
      "Diseñamos procesos alineados con ITIL, implementamos la plataforma y acompañamos su operación. Conectamos incidentes, solicitudes, problemas, cambios y activos en flujos de trabajo trazables.",
    evidence: [processEvidence],
    capabilities: [
      {
        title: "Consultoría ITSM",
        description: "Definición y mejora de procesos alineados con ITIL.",
      },
      {
        title: "Implementación de plataforma",
        description: "IBM Maximo IT y GLPI según el alcance requerido.",
      },
      {
        title: "Automatización de procesos",
        description:
          "Flujos de incidentes, solicitudes, problemas, cambios, activos y CMDB cuando aplique.",
      },
      {
        title: "Administración de plataforma",
        description: "Gestión técnica y funcional de la herramienta.",
      },
      {
        title: "Plataforma cloud administrada",
        description:
          "Operación de la infraestructura cloud que soporta la mesa de servicio.",
      },
    ],
    metrics: [],
    experience:
      "Experiencia interna de nivel ITIL Expert, implementación y administración de IBM Maximo IT y GLPI, y operación de la infraestructura IBM Cloud para mesas de servicio.",
    cases: [],
    technologies: ["IBM Maximo IT", "GLPI", "IBM Cloud"],
    cta: "Evalúa tu operación de TI",
    references: [
      {
        label: "IBM · Maximo IT 9.2, gestión de servicios y activos",
        url: "https://www.ibm.com/docs/en/max-it/cd.0.0_cd?topic=it-whats-new-in-maximo-v92",
      },
    ],
  },
  {
    slug: "managed-services",
    name: "Optimize IT Managed Services",
    shortName: "Managed Services",
    tagline: "Tu tecnología crítica, con un equipo que responde.",
    description:
      "Conocimiento especializado y responsabilidad de servicio para la operación tecnológica.",
    problem:
      "Mantener especialistas de múltiples tecnologías, conservar el conocimiento y atender la operación diaria exige una estructura que va más allá de una persona. Los parches, el monitoreo y los acuerdos de servicio necesitan procesos sostenibles.",
    proposal:
      "Definimos un alcance de servicio, responsabilidades y escalamiento para acompañar la operación de tus plataformas. Sumamos especialistas y procesos para mantener el conocimiento y la continuidad.",
    evidence: [
      engineeringEvidence,
      {
        value: "60 %",
        label: "utiliza proveedores administrados para nube pública",
        context:
          "759 participantes de State of the Cloud 2025; uso de MSP en alguna capacidad, no de todos los servicios de TI.",
        source: "Flexera",
        sourceUrl: flexeraUrl,
        publicationYear: 2025,
      },
    ],
    capabilities: [
      {
        title: "Consultoría especializada",
        description: "Evaluación y acompañamiento técnico de la operación.",
      },
      {
        title: "Platform Management",
        description:
          "Administración de OpenShift, VMware, infraestructura y cloud.",
      },
      {
        title: "Database Management",
        description:
          "Administración y soporte de bases de datos según alcance y capacidades acordadas.",
      },
      {
        title: "Data Protection Operations",
        description: "Operación de plataformas de respaldo y recuperación.",
      },
      {
        title: "Application & Platform Support",
        description:
          "Administración de aplicaciones y plataformas tecnológicas.",
      },
      {
        title: "Soporte y escalamiento",
        description:
          "Atención especializada con responsabilidades y condiciones de servicio definidas.",
      },
    ],
    metrics: [],
    experience:
      "Experiencia operando virtualización, nube y plataformas de protección de información. El horario de cobertura y los SLA se definen para cada servicio.",
    cases: [cases[1]],
    technologies: ["OpenShift", "VMware", "IBM Fusion", "DB2", "Veeam"],
    cta: "Conversemos sobre tu operación tecnológica",
    references: [
      { label: "Flexera · Servicios administrados cloud", url: flexeraUrl },
      {
        label: "New Relic / ETR · Observability Forecast 2025",
        url: newRelicUrl,
      },
    ],
  },
];

export const solutions: Solution[] = originalSolutions.map((s) => {
  const landing = getLanding(s.slug);
  if (!landing) return s;
  return {
    ...s,
    tagline: landing.headline,
    description: landing.description,
    problem: landing.challenge,
    proposal: landing.intro.join(" "),
    capabilities: landing.capabilities,
    technologies: landing.technologies,
    cta: "Solicitar asesoría gratuita",
  };
});
export const corporateMetrics: Metric[] = [
  solutions[0].metrics[0],
  solutions[0].metrics[1],
  solutions[0].metrics[2],
  solutions[3].metrics[0],
];
export const technologies = [
  "IBM",
  "Red Hat",
  "Veeam",
  "Dell",
  "Lenovo",
  "AWS",
  "Microsoft Azure",
  "Wasabi",
].map((name, index) => ({
  name,
  logo: {
    type: "image",
    src:
      "/media/brands/" +
      [
        "ibm.webp",
        "redhat.svg",
        "veeam.svg",
        "dell.svg",
        "lenovo.webp",
        "aws.svg",
        "microsoft.webp",
        "wasabi-white.webp",
      ][index],
    alt:
      name === "Microsoft Azure" ? "Logo Microsoft para Azure" : "Logo " + name,
  } as Media,
}));
