"use client";
import { useState } from "react";
import { landings } from "@/content/landings";
export function AdvisoryForm({ service = "" }: { service?: string }) {
  const [preview, setPreview] = useState(false);
  return (
    <section id="contacto" className="advisory-section shell">
      <div className="advisory-copy">
        <p className="eyebrow">CONVERSEMOS SOBRE SU NECESIDAD</p>
        <h2>Reciba asesoría gratuita.</h2>
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
          Vista previa del formulario. Las solicitudes todavía no se envían.
        </small>
      </div>
      <form
        className="advisory-form"
        onSubmit={(event) => {
          event.preventDefault();
          setPreview(true);
        }}
      >
        <div className="form-pair">
          <label>
            Nombre completo
            <input name="name" autoComplete="name" required />
          </label>
          <label>
            Empresa
            <input name="company" autoComplete="organization" required />
          </label>
        </div>
        <div className="form-pair">
          <label>
            Correo de contacto
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Teléfono <span>(opcional)</span>
            <input name="phone" type="tel" autoComplete="tel" />
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
            required
            placeholder="Describa brevemente su necesidad. No incluya información confidencial."
          />
        </label>
        <button className="button primary" type="submit">
          Solicitar asesoría gratuita <span aria-hidden="true">↗</span>
        </button>
        <p className="form-note">
          Formulario de demostración · no registra ni transmite datos.
        </p>
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
