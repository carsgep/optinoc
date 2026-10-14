"use client";
import { useState, useRef } from "react";
import { landings } from "@/content/landings";
export function AdvisoryForm({ service = "" }: { service?: string }) {
  const endpoint = process.env.NEXT_PUBLIC_CONTACT_ENDPOINT;
  const [preview, setPreview] = useState(false);
  const [sending, setSending] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [failed, setFailed] = useState(false);
  const tokenRef = useRef<{ token: string; requestId: string } | null>(null);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!endpoint) {
      setPreview(true);
      return;
    }
    const form = event.currentTarget;
    setSending(true);
    setFeedback("");
    setFailed(false);
    try {
      if (!tokenRef.current) {
        const init = await fetch(endpoint + "?action=token", {
          credentials: "same-origin",
          cache: "no-store",
        });
        const session = await init.json();
        if (!init.ok || !session.ok || typeof session.token !== "string")
          throw new Error(
            "No pudimos iniciar la solicitud. Inténtelo nuevamente.",
          );
        tokenRef.current = session;
      }
      const fields = Object.fromEntries(new FormData(form));
      const query = new URLSearchParams(window.location.search);
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...fields,
          token: tokenRef.current!.token,
          consent: fields.consent === "on",
          sourcePath: window.location.pathname,
          utmSource: query.get("utm_source")?.slice(0, 200) ?? "",
          utmMedium: query.get("utm_medium")?.slice(0, 200) ?? "",
          utmCampaign: query.get("utm_campaign")?.slice(0, 200) ?? "",
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        if (response.status === 403) tokenRef.current = null;
        throw new Error(
          result.error ??
            "No pudimos registrar su solicitud. Inténtelo nuevamente.",
        );
      }
      setFeedback(
        "Gracias. Recibimos su solicitud. Un especialista de Optimize IT se pondrá en contacto por los datos registrados.",
      );
      tokenRef.current = null;
      form.reset();
    } catch (error) {
      setFailed(true);
      setFeedback(
        error instanceof Error
          ? error.message
          : "No pudimos registrar su solicitud. Inténtelo nuevamente.",
      );
    } finally {
      setSending(false);
    }
  }
  return (
    <section id="contacto" className="advisory-section shell">
      <div className="advisory-copy">
        <p className="eyebrow">CONVERSEMOS SOBRE SU NECESIDAD</p>
        <h2>Conversemos sobre su necesidad de TI</h2>
        <p>
          Cuéntenos qué necesita proteger, administrar o mejorar. Un
          especialista de Optimize IT podrá orientarlo sobre los próximos pasos.
        </p>
        <div className="advisory-facts">
          <span>01 · Su necesidad</span>
          <span>02 · La conversación</span>
          <span>03 · Los próximos pasos</span>
        </div>
        <small>
          {endpoint
            ? "Su solicitud será atendida por el equipo de Optimize IT."
            : "Vista previa del formulario. Las solicitudes todavía no se envían."}
        </small>
      </div>
      <form className="advisory-form" onSubmit={submit}>
        <div className="form-pair">
          <label>
            Nombre completo
            <input name="name" autoComplete="name" maxLength={120} required />
          </label>
          <label>
            Empresa
            <input
              name="company"
              autoComplete="organization"
              maxLength={160}
              required
            />
          </label>
        </div>
        <div className="form-pair">
          <label>
            Correo de contacto
            <input
              name="email"
              type="email"
              autoComplete="email"
              maxLength={254}
              required
            />
          </label>
          <label>
            Teléfono <span>(opcional)</span>
            <input name="phone" type="tel" autoComplete="tel" maxLength={40} />
          </label>
        </div>
        <label>
          Servicio de interés
          <select name="service" defaultValue={service} required>
            <option value="">Seleccione una solución</option>
            {landings.map((s) => (
              <option key={s.slug} value={s.slug}>
                {s.shortName}
              </option>
            ))}
          </select>
        </label>
        <label>
          ¿Qué necesita resolver?
          <textarea
            name="need"
            rows={4}
            maxLength={3500}
            required
            placeholder="Describa brevemente su necesidad. No incluya información confidencial."
          />
        </label>
        {endpoint && (
          <>
            <label className="contact-honeypot" aria-hidden="true">
              Website
              <input name="website" tabIndex={-1} autoComplete="off" />
            </label>
            <label className="contact-consent">
              <input type="checkbox" name="consent" required />
              Autorizo el tratamiento de mis datos para atender esta solicitud
              conforme a la{" "}
              <a
                href="https://optimizeit.co/politica-de-privacidad/"
                target="_blank"
                rel="noopener noreferrer"
              >
                política de privacidad
              </a>
              .
            </label>
          </>
        )}
        <button
          className="button primary"
          type="submit"
          disabled={sending}
          aria-busy={sending}
        >
          {sending ? "Enviando su solicitud…" : "Solicitar asesoría"}{" "}
          <span aria-hidden="true">↗</span>
        </button>
        <p className="form-note">
          {endpoint
            ? "Los datos se utilizan para gestionar su solicitud de asesoría."
            : "Formulario de demostración · no registra ni transmite datos."}
        </p>
        {feedback && (
          <p
            role={failed ? "alert" : "status"}
            className="form-preview-message"
          >
            {feedback}
          </p>
        )}
        {preview && (
          <p role="status" className="form-preview-message">
            La demostración está completa. No se ha enviado su solicitud. El
            canal de contacto se conectará antes del lanzamiento.
          </p>
        )}
      </form>
    </section>
  );
}
