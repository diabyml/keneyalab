import { useMemo } from "react"
import type { ReportSnapshot, ReportTemplateSnapshot } from "./reportTypes"
import { SandboxRenderer } from "./SandboxRenderer"

function valueAt(source: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>((value, key) => {
    if (!value || typeof value !== "object") return ""
    return (value as Record<string, unknown>)[key]
  }, source)
}

function escapeHtml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

function interpolate(html: string, snapshot: ReportSnapshot) {
  return html.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_, path: string) => {
    return escapeHtml(valueAt(snapshot, path))
  })
}

export function ReportDocument({
  snapshot,
  templates,
  voided = false,
}: {
  snapshot: ReportSnapshot
  templates: ReportTemplateSnapshot
  voided?: boolean
}) {
  const header = useMemo(
    () => interpolate(templates.header.html_source, snapshot),
    [snapshot, templates.header.html_source],
  )
  const details = useMemo(
    () => interpolate(templates.details.html_source, snapshot),
    [snapshot, templates.details.html_source],
  )
  const footer = useMemo(
    () => interpolate(templates.footer.html_source, snapshot),
    [snapshot, templates.footer.html_source],
  )

  return (
    <article className="report-a4 relative mx-auto min-h-[297mm] w-[210mm] bg-white p-[14mm] text-slate-900 shadow-sm print:min-h-0 print:w-auto print:p-0 print:shadow-none">
      <style>{`${templates.header.css_source}\n${templates.details.css_source}\n${templates.footer.css_source}`}</style>
      {voided && (
        <div className="absolute inset-x-0 top-[42%] z-10 -rotate-12 text-center text-7xl font-black tracking-[0.2em] text-red-600/15">
          ANNULÉ
        </div>
      )}
      {/* biome-ignore lint/security/noDangerouslySetInnerHtml: report HTML is allowlist-sanitized by the backend before storage */}
      <div dangerouslySetInnerHTML={{ __html: header }} />
      {/* biome-ignore lint/security/noDangerouslySetInnerHtml: report HTML is allowlist-sanitized by the backend before storage */}
      <div dangerouslySetInnerHTML={{ __html: details }} />
      <main className="min-h-[190mm]">
        {snapshot.categories.map((category) => {
          const key = category.id ?? "uncategorized"
          const renderer =
            templates.renderers[key] ?? templates.renderers.uncategorized
          return renderer ? (
            <SandboxRenderer
              key={key}
              source={renderer.jsx_source}
              css={renderer.css_source}
              category={category}
            />
          ) : (
            <p key={key}>Aucun rendu publié pour {category.name}.</p>
          )
        })}
      </main>
      {/* biome-ignore lint/security/noDangerouslySetInnerHtml: report HTML is allowlist-sanitized by the backend before storage */}
      <div dangerouslySetInnerHTML={{ __html: footer }} />
    </article>
  )
}
