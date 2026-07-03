import { AlertTriangle } from "lucide-react"
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react"

import {
  buildReportDocumentHtml,
  buildReportDocumentModel,
  type CompiledRenderer,
} from "./reportDocumentBuilder"
import type {
  ReportRenderConfig,
  ReportSnapshot,
  ReportTemplateSnapshot,
} from "./reportTypes"
import { compileReportRenderer } from "./SandboxRenderer"

type ReportDocumentProps = {
  snapshot: ReportSnapshot
  templates: ReportTemplateSnapshot
  renderConfig?: Partial<ReportRenderConfig> | null
  voided?: boolean
  onReadyChange?: (ready: boolean) => void
}

export type ReportDocumentHandle = {
  print: () => void
}

export const ReportDocument = forwardRef<
  ReportDocumentHandle,
  ReportDocumentProps
>(function ReportDocument(
  { snapshot, templates, renderConfig, voided = false, onReadyChange },
  ref,
) {
  const frameRef = useRef<HTMLIFrameElement>(null)
  const [compiledRenderers, setCompiledRenderers] = useState<
    CompiledRenderer[] | null
  >(null)
  const [compileError, setCompileError] = useState("")
  const [renderError, setRenderError] = useState("")
  const [iframeReady, setIframeReady] = useState(false)
  const [height, setHeight] = useState(980)

  const documentModel = useMemo(
    () => buildReportDocumentModel({ snapshot, templates, renderConfig: null }),
    [snapshot, templates],
  )
  const updateModel = useMemo(
    () => buildReportDocumentModel({ snapshot, templates, renderConfig }),
    [snapshot, templates, renderConfig],
  )

  useImperativeHandle(
    ref,
    () => ({
      print: () => {
        const win = frameRef.current?.contentWindow
        if (!win || compileError || renderError) return
        win.postMessage({ type: "report-document-print" }, "*")
      },
    }),
    [compileError, renderError],
  )

  useEffect(() => {
    let active = true
    setCompileError("")
    setRenderError("")
    setIframeReady(false)
    setCompiledRenderers(null)
    onReadyChange?.(false)

    const rendererJobs = documentModel.rendererEntries.map(async (entry) => ({
      key: entry.key,
      code: await compileReportRenderer(entry.renderer.jsx_source),
      css: entry.renderer.css_source,
    }))

    Promise.all(rendererJobs)
      .then((compiled) => {
        if (active) setCompiledRenderers(compiled)
      })
      .catch((error: Error) => {
        if (!active) return
        setCompileError(error.message)
        onReadyChange?.(false)
      })

    return () => {
      active = false
    }
  }, [documentModel.rendererEntries, onReadyChange])

  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (event.source !== frameRef.current?.contentWindow) return
      if (event.data?.type === "report-document-height") {
        setHeight(Math.max(980, Number(event.data.height) + 8))
      }
      if (event.data?.type === "report-document-ready") {
        setIframeReady(true)
        setRenderError("")
      }
      if (event.data?.type === "report-document-updated") {
        setRenderError("")
        onReadyChange?.(true)
      }
      if (event.data?.type === "report-document-error") {
        setIframeReady(false)
        setRenderError(event.data.message)
        onReadyChange?.(false)
      }
    }
    window.addEventListener("message", receive)
    return () => window.removeEventListener("message", receive)
  }, [onReadyChange])

  const srcDoc = useMemo(
    () =>
      compileError || !compiledRenderers
        ? ""
        : buildReportDocumentHtml({
            compiledRenderers,
            header: documentModel.header,
            details: documentModel.details,
            footer: documentModel.footer,
            componentCss: documentModel.componentCss,
            voided,
          }),
    [
      compileError,
      compiledRenderers,
      documentModel.header,
      documentModel.details,
      documentModel.footer,
      documentModel.componentCss,
      voided,
    ],
  )

  useEffect(() => {
    setIframeReady(false)
    if (srcDoc) {
      onReadyChange?.(false)
    }
  }, [srcDoc, onReadyChange])

  useEffect(() => {
    const win = frameRef.current?.contentWindow
    if (!win || !iframeReady || compileError || renderError) return
    win.postMessage(
      {
        type: "report-document-update-config",
        payload: updateModel.updatePayload,
      },
      "*",
    )
  }, [compileError, iframeReady, renderError, updateModel.updatePayload])

  if (compileError || renderError) {
    return (
      <div className="mx-auto flex max-w-[210mm] gap-2 border border-red-200 bg-red-50 p-3 text-xs text-red-800">
        <AlertTriangle className="mt-0.5 size-4 shrink-0" />
        <div>
          <strong>Le rendu personnalisé a échoué.</strong>
          <p className="mt-1 font-mono">{compileError || renderError}</p>
        </div>
      </div>
    )
  }

  return (
    <iframe
      ref={frameRef}
      title="Aperçu du compte rendu"
      sandbox="allow-scripts allow-modals"
      srcDoc={srcDoc}
      className="mx-auto block w-[210mm] min-w-[210mm] border-0 bg-transparent"
      scrolling="no"
      style={{ height }}
    />
  )
})
