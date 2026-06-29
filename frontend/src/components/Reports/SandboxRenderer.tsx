import { AlertTriangle } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import { cn } from "@/lib/utils"
import type { ReportCategory } from "./reportTypes"

type CompilerResponse = { id: string; code?: string; error?: string }

let compiler: Worker | null = null
const pending = new Map<
  string,
  { resolve: (value: string) => void; reject: (reason: Error) => void }
>()

function getCompiler() {
  compiler ??= new Worker(
    new URL("./rendererCompiler.worker.ts", import.meta.url),
    {
      type: "module",
    },
  )
  compiler.onmessage = (event: MessageEvent<CompilerResponse>) => {
    const request = pending.get(event.data.id)
    if (!request) return
    pending.delete(event.data.id)
    if (event.data.error) request.reject(new Error(event.data.error))
    else request.resolve(event.data.code ?? "")
  }
  return compiler
}

export function compileReportRenderer(source: string) {
  return new Promise<string>((resolve, reject) => {
    const id = crypto.randomUUID()
    pending.set(id, { resolve, reject })
    getCompiler().postMessage({ id, source })
  })
}

function safeJson(value: unknown) {
  return JSON.stringify(value).replace(/</g, "\\u003c")
}

function createDocument(code: string, css: string, category: ReportCategory) {
  const runtime = `
    const Fragment = Symbol("Fragment");
    function append(parent, child) {
      if (child == null || child === false || child === true) return;
      if (Array.isArray(child)) return child.forEach(item => append(parent, item));
      parent.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    function h(type, props, ...children) {
      const values = props || {};
      if (type === Fragment) {
        const fragment = document.createDocumentFragment();
        children.forEach(child => append(fragment, child));
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
      children.forEach(child => append(element, child));
      return element;
    }
    const ReportKit = {
      ClinicalTable({ category }) {
        const section = h("section", { className: "report-category" },
          h("h2", null, category.name),
          h("table", { className: "clinical-table" },
            h("thead", null, h("tr", null,
              h("th", null, "Analyse"), h("th", null, "Résultat"),
              h("th", null, "Unité"), h("th", null, "Valeurs de référence")
            )),
            h("tbody", null, ...category.tests.flatMap(test => [
              test.analytes.length > 1
                ? h("tr", { className: "report-test-heading" },
                    h("th", { colSpan: 4 }, test.catalog_name)
                  )
                : null,
              ...test.analytes.map(analyte => h("tr", null,
                h("td", null, analyte.analyte_name),
                h("td", { className: analyte.is_critical ? "result-critical" : analyte.is_abnormal ? "result-abnormal" : "" },
                  analyte.data_type === "image" && analyte.image_url
                    ? h("img", { src: analyte.image_url, alt: analyte.analyte_name, className: "report-result-image" })
                    : analyte.result_value || "—",
                  ...(analyte.comments || []).map(comment => h("small", { className: "result-comment" }, comment.comment))
                ),
                h("td", null, analyte.unit_name || "—"),
                h("td", null, analyte.reference_text || "—")
              ))
            ]))
          )
        );
        return section;
      }
    };
    function reportHeight() {
      const root = document.getElementById("root");
      const height = Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight,
        root ? root.scrollHeight : 0,
        root ? root.getBoundingClientRect().height : 0
      );
      parent.postMessage({ type: "report-renderer-ready", height }, "*");
    }
    function scheduleHeightReports() {
      reportHeight();
      requestAnimationFrame(() => {
        reportHeight();
        requestAnimationFrame(reportHeight);
      });
    }
    const category = ${safeJson(category)};
    try {
      ${code}
      const renderer = globalThis.__ReportRenderer;
      if (typeof renderer !== "function") throw new Error("Le composant Renderer est introuvable.");
      append(document.getElementById("root"), renderer({ category, ReportKit }));
      if ("ResizeObserver" in window) {
        const observer = new ResizeObserver(scheduleHeightReports);
        observer.observe(document.documentElement);
        observer.observe(document.body);
        observer.observe(document.getElementById("root"));
      }
      window.addEventListener("load", scheduleHeightReports);
      scheduleHeightReports();
    } catch (error) {
      parent.postMessage({ type: "report-renderer-error", message: error?.message || String(error) }, "*");
    }
  `
  return `<!doctype html>
  <html><head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: https:; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
    <style>html,body{margin:0;background:transparent;color:#000;font:11px Inter,Arial,sans-serif;overflow:hidden}*{box-sizing:border-box}h3{font-size:11px;margin:10px 0 4px}.report-result-image{max-width:180px;max-height:100px}.result-comment{display:block;margin-top:3px;color:#000;font-style:italic}${css}#root,#root *{color:#000}#root strong,#root b{font-weight:700}#root table,#root th,#root td{border-color:#374151}.result-abnormal,.result-abnormal *,.result-critical,.result-critical *{color:#b91c1c;font-weight:700}</style>
  </head><body><div id="root"></div><script>${runtime.replace(/<\/script>/g, "<\\/script>")}</script></body></html>`
}

export function SandboxRenderer({
  source,
  css,
  category,
  className,
}: {
  source: string
  css: string
  category: ReportCategory
  className?: string
}) {
  const frameRef = useRef<HTMLIFrameElement>(null)
  const [compiled, setCompiled] = useState("")
  const [error, setError] = useState("")
  const [height, setHeight] = useState(120)

  useEffect(() => {
    let active = true
    setError("")
    compileReportRenderer(source)
      .then((code) => {
        if (active) setCompiled(code)
      })
      .catch((reason: Error) => {
        if (active) setError(reason.message)
      })
    return () => {
      active = false
    }
  }, [source])

  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (event.source !== frameRef.current?.contentWindow) return
      if (event.data?.type === "report-renderer-ready") {
        setHeight(Math.max(80, Number(event.data.height) + 4))
      }
      if (event.data?.type === "report-renderer-error") {
        setError(event.data.message)
      }
    }
    window.addEventListener("message", receive)
    return () => window.removeEventListener("message", receive)
  }, [])

  const srcDoc = useMemo(
    () => (compiled ? createDocument(compiled, css, category) : ""),
    [category, compiled, css],
  )

  useEffect(() => {
    if (srcDoc) setHeight(120)
  }, [srcDoc])

  if (error) {
    return (
      <div className="flex gap-2 border border-red-200 bg-red-50 p-3 text-xs text-red-800">
        <AlertTriangle className="mt-0.5 size-4 shrink-0" />
        <div>
          <strong>Le rendu personnalisé a échoué.</strong>
          <p className="mt-1 font-mono">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <iframe
      ref={frameRef}
      title={`Rendu ${category.name}`}
      sandbox="allow-scripts"
      srcDoc={srcDoc}
      className={cn("block w-full border-0 bg-transparent", className)}
      scrolling="no"
      style={{ height }}
    />
  )
}
