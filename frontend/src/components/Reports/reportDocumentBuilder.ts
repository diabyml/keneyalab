import type {
  RendererTemplate,
  ReportCategory,
  ReportRenderConfig,
  ReportSnapshot,
  ReportTemplateSnapshot,
} from "./reportTypes"
import {
  applyReportRenderConfig,
  normalizeReportRenderConfig,
  reportCategoryKey,
} from "./reportTypes"

export type CategoryRenderEntry = {
  kind: "category"
  key: string
  category: ReportCategory
  renderer: RendererTemplate | null
  pageBreak: boolean
}

export type InterpretationRenderEntry = {
  kind: "interpretation"
  key: "interpretation"
  pageBreak: boolean
}

export type SectionRenderEntry = CategoryRenderEntry | InterpretationRenderEntry

export type CompiledRenderer = {
  key: string
  code: string
  css: string
}

export type ReportDocumentUpdatePayload = {
  sections: Array<
    | {
        kind: "category"
        key: string
        name: string
        category: ReportCategory
        pageBreak: boolean
        rendererMissing: boolean
      }
    | {
        kind: "interpretation"
        key: "interpretation"
        pageBreak: boolean
      }
  >
  footerSpacingMm: number
  interpretationHtml: string
}

export const REPORT_COMPONENT_TEXT_STYLES = `
  .report-component-content,
  .report-component-content * {
    color: #000;
  }

  .report-component-content strong,
  .report-component-content b {
    font-weight: 700;
  }
`

export const REPORT_DOCUMENT_BASE_STYLES = `
  @page {
    size: A4 portrait;
  }

  html,
  body {
    margin: 0;
    min-height: 100%;
    background: #f1f5f9;
    color: #000;
    font: 11px Inter, Arial, sans-serif;
  }

  * {
    box-sizing: border-box;
  }

  .report-sheet {
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto 24px;
    padding: 14mm 14mm 14mm;
    background: #fff;
    box-shadow: 0 1px 8px rgb(15 23 42 / 0.16);
    color: #000;
  }

  .report-main {
    min-height: 190mm;
  }

  .report-interpretation {
    margin-top: 10px;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .report-interpretation h2 {
    margin: 10px 0 6px;
    border-bottom: 1px solid #cbd5e1;
    color: #0f172a;
    font-size: 12px;
  }

  .report-interpretation-content {
    font-size: 11px;
    line-height: 1.45;
  }

  .report-interpretation-content table {
    width: 100%;
    border-collapse: collapse;
  }

  .report-interpretation-content td,
  .report-interpretation-content th {
    border: 1px solid #374151;
    padding: 3px 5px;
  }

  .report-interpretation-content ul,
  .report-interpretation-content ol {
    padding-left: 18px;
  }

  .report-category-section {
    display: block;
  }

  .report-category-section + .report-category-section {
    margin-top: 8px;
  }

  .report-category-force-break {
    break-before: page;
    page-break-before: always;
  }

  .report-interpretation-force-break {
    break-before: page;
    page-break-before: always;
  }

  .report-missing-renderer,
  .report-renderer-error {
    border: 1px solid #fecaca;
    background: #fef2f2;
    color: #991b1b;
    padding: 10px;
    font-size: 11px;
  }

  .report-voided-watermark {
    position: fixed;
    inset-inline: 0;
    top: 42%;
    z-index: 10;
    transform: rotate(-12deg);
    color: rgb(220 38 38 / 0.15);
    font-size: 72px;
    font-weight: 900;
    letter-spacing: 0.2em;
    text-align: center;
    pointer-events: none;
  }

  @media print {
    html,
    body {
      width: auto;
      min-height: 0;
      background: #fff;
    }

    .report-sheet {
      width: auto;
      min-height: 0;
      margin: 0;
      padding: 0;
      box-shadow: none;
    }

    .report-category-section + .report-category-section {
      margin-top: 0;
    }

    .report-category-force-break {
      break-before: page;
      page-break-before: always;
    }

    .report-interpretation-force-break {
      break-before: page;
      page-break-before: always;
    }

    tr,
    img {
      break-inside: avoid;
      page-break-inside: avoid;
    }
  }
`

export const RENDERER_BASE_STYLES = `
  :host {
    display: block;
    color: #000;
    font: 11px Inter, Arial, sans-serif;
  }

  * {
    box-sizing: border-box;
  }

  h3 {
    margin: 10px 0 4px;
    font-size: 11px;
  }

  table,
  th,
  td {
    border-color: #374151;
  }

  strong,
  b {
    font-weight: 700;
  }

  .report-result-image {
    max-width: 180px;
    max-height: 100px;
  }

  .result-abnormal,
  .result-abnormal *,
  .result-critical,
  .result-critical * {
    color: #b91c1c;
    font-weight: 700;
  }
`

export function valueAt(source: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>((value, key) => {
    if (!value || typeof value !== "object") return ""
    return (value as Record<string, unknown>)[key]
  }, source)
}

export function escapeHtml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

export function interpolate(html: string, snapshot: ReportSnapshot) {
  return html.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_, path: string) => {
    return escapeHtml(valueAt(snapshot, path))
  })
}

export function safeJson(value: unknown) {
  return JSON.stringify(value).replace(/</g, "\\u003c")
}

export function safeScript(value: string) {
  return value.replace(/<\/script>/gi, "<\\/script>")
}

function rendererRegistrationScript(compiledRenderers: CompiledRenderer[]) {
  return compiledRenderers
    .map(
      (renderer) => `
        registerRenderer(${safeJson(renderer.key)}, () => {
          ${renderer.code}
        });
      `,
    )
    .join("\n")
}

export function buildReportDocumentHtml({
  compiledRenderers,
  header,
  details,
  footer,
  componentCss,
  voided,
}: {
  compiledRenderers: CompiledRenderer[]
  header: string
  details: string
  footer: string
  componentCss: string
  voided: boolean
}) {
  const rendererCssByKey = Object.fromEntries(
    compiledRenderers.map((renderer) => [renderer.key, renderer.css]),
  )
  const registrationScript = rendererRegistrationScript(compiledRenderers)
  const runtime = `
    const Fragment = Symbol("Fragment");
    const renderers = {};
    const rendererErrors = {};
    const rendererCssByKey = ${safeJson(rendererCssByKey)};
    const footerHtml = ${safeJson(footer)};
    const sectionNodes = new Map();
    let footerNode = null;
    let interpretationNode = null;
    let interpretationHtml = "";

    function append(parent, child) {
      if (child == null || child === false || child === true) return;
      if (Array.isArray(child)) return child.forEach((item) => append(parent, item));
      parent.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }

    function h(type, props, ...children) {
      const values = props || {};
      if (type === Fragment) {
        const fragment = document.createDocumentFragment();
        children.forEach((child) => append(fragment, child));
        return fragment;
      }
      if (typeof type === "function") return type({ ...values, children });
      const element = document.createElement(type);
      for (const [key, value] of Object.entries(values)) {
        if (key === "className") element.className = value || "";
        else if (key === "style" && value && typeof value === "object") Object.assign(element.style, value);
        else if (key.startsWith("on") && typeof value === "function") element.addEventListener(key.slice(2).toLowerCase(), value);
        else if (key !== "children" && value != null && value !== false) element.setAttribute(key, String(value));
      }
      children.forEach((child) => append(element, child));
      return element;
    }

    const ReportKit = {
      ClinicalTable({ category }) {
        return h("section", { className: "report-category" },
          h("h2", null, category.name),
          h("table", { className: "clinical-table" },
            h("thead", null, h("tr", null,
              h("th", null, "Analyse"), h("th", null, "Résultat"),
              h("th", null, "Unité"), h("th", null, "Valeurs de référence")
            )),
            h("tbody", null, ...category.tests.flatMap((test) => [
              test.analytes.length > 1
                ? h("tr", { className: "report-test-heading" },
                    h("th", { colSpan: 4 }, test.catalog_name)
                  )
                : null,
              ...test.analytes.map((analyte) => h("tr", null,
                h("td", null, analyte.analyte_name),
                h("td", { className: analyte.is_critical ? "result-critical" : analyte.is_abnormal ? "result-abnormal" : "" },
                  analyte.data_type === "image" && analyte.image_url
                    ? h("img", { src: analyte.image_url, alt: analyte.analyte_name, className: "report-result-image" })
                    : analyte.result_value || "—"
                ),
                h("td", null, analyte.unit_name || "—"),
                h("td", null, analyte.reference_text || "—")
              ))
            ]))
          )
        );
      }
    };

    function registerRenderer(key, run) {
      try {
        globalThis.__ReportRenderer = null;
        run();
        const renderer = globalThis.__ReportRenderer;
        if (typeof renderer !== "function") {
          throw new Error("Le composant Renderer est introuvable.");
        }
        renderers[key] = renderer;
      } catch (error) {
        rendererErrors[key] = error?.message || String(error);
      }
    }

    ${registrationScript}

    function reportHeight() {
      const sheet = document.querySelector(".report-sheet");
      const height = Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight,
        sheet ? sheet.scrollHeight : 0,
        sheet ? sheet.getBoundingClientRect().height : 0
      );
      parent.postMessage({ type: "report-document-height", height }, "*");
    }

    function reportReady() {
      parent.postMessage({ type: "report-document-ready" }, "*");
      reportHeight();
    }

    function reportError(message) {
      parent.postMessage({ type: "report-document-error", message }, "*");
      reportHeight();
    }

    function printReport() {
      window.focus();
      window.print();
    }

    function scheduleHeightReports() {
      reportHeight();
      requestAnimationFrame(() => {
        reportHeight();
        requestAnimationFrame(reportHeight);
      });
    }

    function sectionClassName(kind, pageBreak) {
      if (kind === "interpretation") {
        return pageBreak
          ? "report-interpretation report-interpretation-force-break"
          : "report-interpretation";
      }
      return pageBreak
        ? "report-category-section report-category-force-break"
        : "report-category-section";
    }

    function renderCategory(entry) {
      const section = document.createElement("section");
      section.className = sectionClassName("category", entry.pageBreak);
      section.dataset.sectionKey = entry.key;

      if (entry.rendererMissing) {
        section.innerHTML = '<p class="report-missing-renderer">Aucun rendu publié pour ' + entry.name + '.</p>';
        return section;
      }

      if (rendererErrors[entry.key]) {
        section.innerHTML = '<div class="report-renderer-error"><strong>Le rendu personnalisé a échoué.</strong><p>' + rendererErrors[entry.key] + '</p></div>';
        return section;
      }

      const renderer = renderers[entry.key];
      if (typeof renderer !== "function") {
        section.innerHTML = '<div class="report-renderer-error"><strong>Le rendu personnalisé a échoué.</strong><p>Le composant Renderer est introuvable.</p></div>';
        return section;
      }

      const host = document.createElement("div");
      const shadow = host.attachShadow({ mode: "open" });
      const style = document.createElement("style");
      style.textContent = ${safeJson(RENDERER_BASE_STYLES)} + "\\n" + (rendererCssByKey[entry.key] || "");
      shadow.append(style);
      append(shadow, renderer({ category: entry.category, ReportKit }));
      section.append(host);
      return section;
    }

    function getCategorySection(entry) {
      const signature = JSON.stringify({
        name: entry.name,
        category: entry.category,
        rendererMissing: entry.rendererMissing,
        rendererError: rendererErrors[entry.key] || "",
      });
      const existing = sectionNodes.get(entry.key);
      if (existing && existing.dataset.signature === signature) {
        existing.className = sectionClassName("category", entry.pageBreak);
        return existing;
      }
      const next = renderCategory(entry);
      next.dataset.signature = signature;
      sectionNodes.set(entry.key, next);
      return next;
    }

    function getInterpretationSection(entry) {
      if (!interpretationHtml) return null;
      if (interpretationNode) {
        interpretationNode.className = sectionClassName("interpretation", entry.pageBreak);
        return interpretationNode;
      }
      const section = document.createElement("section");
      section.className = sectionClassName("interpretation", entry.pageBreak);
      section.dataset.sectionKey = entry.key;
      section.innerHTML = '<h2>Interprétation</h2><div class="report-interpretation-content">' + interpretationHtml + '</div>';
      interpretationNode = section;
      return section;
    }

    function getFooter(spacingMm) {
      if (!footerNode) {
        footerNode = document.createElement("div");
        footerNode.className = "report-component-content";
        footerNode.innerHTML = footerHtml;
      }
      footerNode.style.marginTop = spacingMm + "mm";
      return footerNode;
    }

    function applyReportUpdate(payload) {
      const main = document.getElementById("report-main");
      if (!main) throw new Error("La zone principale du rapport est introuvable.");

      interpretationHtml = payload.interpretationHtml || "";
      const fragment = document.createDocumentFragment();
      let footerAppended = false;
      const visibleKeys = new Set();

      payload.sections.forEach((entry) => {
        if (entry.kind === "interpretation") {
          const interpretation = getInterpretationSection(entry);
          if (!interpretation) return;
          fragment.append(interpretation, getFooter(payload.footerSpacingMm));
          footerAppended = true;
          visibleKeys.add(entry.key);
          return;
        }

        const section = getCategorySection(entry);
        fragment.append(section);
        visibleKeys.add(entry.key);
      });

      for (const [key, node] of sectionNodes.entries()) {
        if (!visibleKeys.has(key)) {
          node.remove();
          sectionNodes.delete(key);
        }
      }
      if (!visibleKeys.has("interpretation")) {
        interpretationNode?.remove();
        interpretationNode = null;
      }
      if (!footerAppended) {
        fragment.append(getFooter(payload.footerSpacingMm));
      }

      main.replaceChildren(fragment);
      scheduleHeightReports();
      parent.postMessage({ type: "report-document-updated" }, "*");
    }

    try {
      if ("ResizeObserver" in window) {
        const observer = new ResizeObserver(scheduleHeightReports);
        observer.observe(document.documentElement);
        observer.observe(document.body);
        observer.observe(document.querySelector(".report-sheet"));
      }
      window.addEventListener("message", (event) => {
        if (event.data?.type === "report-document-print") printReport();
        if (event.data?.type === "report-document-update-config") {
          try {
            applyReportUpdate(event.data.payload);
          } catch (error) {
            reportError(error?.message || String(error));
          }
        }
      });
      window.addEventListener("load", scheduleHeightReports);
      reportReady();
    } catch (error) {
      reportError(error?.message || String(error));
    }
  `

  return `<!doctype html>
  <html>
    <head>
      <meta charset="utf-8">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: http: https:; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
      <style>${REPORT_DOCUMENT_BASE_STYLES}\n${componentCss}\n${REPORT_COMPONENT_TEXT_STYLES}</style>
    </head>
    <body>
      <article class="report-sheet">
        ${
          voided
            ? '<div class="report-voided-watermark" aria-hidden="true">ANNULÉ</div>'
            : ""
        }
        <div class="report-component-content">${header}</div>
        <div class="report-component-content">${details}</div>
        <main id="report-main" class="report-main"></main>
      </article>
      <script>${safeScript(runtime)}</script>
    </body>
  </html>`
}

export function buildReportDocumentModel({
  snapshot,
  templates,
  renderConfig,
}: {
  snapshot: ReportSnapshot
  templates: ReportTemplateSnapshot
  renderConfig?: Partial<ReportRenderConfig> | null
}) {
  const normalizedRenderConfig = normalizeReportRenderConfig(renderConfig)
  const renderedSnapshot = applyReportRenderConfig(snapshot, normalizedRenderConfig)
  const hasInterpretation = Boolean(renderedSnapshot.interpretation?.html)
  const categoryEntries = renderedSnapshot.categories.map((category) => {
    const key = reportCategoryKey(category)
    return {
      kind: "category" as const,
      key,
      category,
      renderer: templates.renderers[key] ?? templates.renderers.uncategorized,
      pageBreak: normalizedRenderConfig.category_page_breaks[key] === true,
    }
  })
  const entriesByKey = new Map<string, SectionRenderEntry>(
    categoryEntries.map((entry) => [entry.key, entry]),
  )
  if (hasInterpretation) {
    entriesByKey.set("interpretation", {
      kind: "interpretation",
      key: "interpretation",
      pageBreak: normalizedRenderConfig.interpretation_page_break,
    })
  }
  const orderedKeys = [
    ...normalizedRenderConfig.section_order.filter(
      (key) => key !== "footer" && entriesByKey.has(key),
    ),
    ...categoryEntries
      .map((entry) => entry.key)
      .filter((key) => !normalizedRenderConfig.section_order.includes(key)),
    ...(hasInterpretation &&
    !normalizedRenderConfig.section_order.includes("interpretation")
      ? ["interpretation"]
      : []),
  ]
  const sections = orderedKeys
    .map((key) => entriesByKey.get(key))
    .filter((entry): entry is SectionRenderEntry => Boolean(entry))
    .map((entry, index) => ({
      ...entry,
      pageBreak: entry.pageBreak && index > 0,
    }))
  const rendererEntries = snapshot.categories
    .map((category) => {
      const key = reportCategoryKey(category)
      return {
        key,
        renderer: templates.renderers[key] ?? templates.renderers.uncategorized,
      }
    })
    .filter((entry): entry is { key: string; renderer: RendererTemplate } =>
      Boolean(entry.renderer),
    )
  const header = interpolate(templates.header.html_source, snapshot)
  const details = interpolate(templates.details.html_source, snapshot)
  const footer = interpolate(templates.footer.html_source, snapshot)
  const componentCss = [
    templates.header.css_source,
    templates.details.css_source,
    templates.footer.css_source,
  ].join("\n")
  const interpretationHtml = renderedSnapshot.interpretation?.html ?? ""
  const updatePayload: ReportDocumentUpdatePayload = {
    sections: sections.map((entry) =>
      entry.kind === "interpretation"
        ? {
            kind: "interpretation",
            key: entry.key,
            pageBreak: entry.pageBreak,
          }
        : {
            kind: "category",
            key: entry.key,
            name: entry.category.name,
            category: entry.category,
            pageBreak: entry.pageBreak,
            rendererMissing: !entry.renderer,
          },
    ),
    footerSpacingMm: normalizedRenderConfig.footer_spacing_mm,
    interpretationHtml,
  }

  return {
    normalizedRenderConfig,
    renderedSnapshot,
    sections,
    rendererEntries,
    header,
    details,
    footer,
    componentCss,
    interpretationHtml,
    updatePayload,
  }
}
