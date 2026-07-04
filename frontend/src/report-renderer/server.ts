import { chromium, type Browser } from "@playwright/test"
import * as esbuild from "esbuild-wasm"

import {
  buildReportDocumentHtml,
  buildReportDocumentModel,
  type CompiledRenderer,
} from "../components/Reports/reportDocumentBuilder"
import type {
  ReportRenderConfig,
  ReportSnapshot,
  ReportTemplateSnapshot,
} from "../components/Reports/reportTypes"

declare const Bun: {
  serve: (options: {
    hostname: string
    port: number
    fetch: (request: Request) => Response | Promise<Response>
  }) => unknown
}

type RenderReportRequest = {
  snapshot: ReportSnapshot
  template_snapshot: ReportTemplateSnapshot
  render_config?: Partial<ReportRenderConfig> | null
  voided?: boolean
}

let browserPromise: Promise<Browser> | null = null
let esbuildInitialized: Promise<void> | null = null

function getBrowser() {
  browserPromise ??= chromium.launch({
    args: ["--disable-dev-shm-usage"],
  })
  return browserPromise
}

async function initializeCompiler() {
  esbuildInitialized ??= esbuild.initialize({})
  return esbuildInitialized
}

async function compileReportRenderer(source: string) {
  await initializeCompiler()
  const result = await esbuild.transform(
    `globalThis.__ReportRenderer = (() => {
      ${source}
      return typeof Renderer === "function" ? Renderer : null;
    })();`,
    {
      loader: "jsx",
      format: "iife",
      target: "es2020",
      jsxFactory: "h",
      jsxFragment: "Fragment",
    },
  )
  return result.code
}

function jsonResponse(status: number, payload: Record<string, unknown>) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

async function renderReportPdf(payload: RenderReportRequest) {
  const model = buildReportDocumentModel({
    snapshot: payload.snapshot,
    templates: payload.template_snapshot,
    renderConfig: payload.render_config,
  })
  const compiledRenderers: CompiledRenderer[] = await Promise.all(
    model.rendererEntries.map(async (entry) => ({
      key: entry.key,
      code: await compileReportRenderer(entry.renderer.jsx_source),
      css: entry.renderer.css_source,
    })),
  )
  const html = buildReportDocumentHtml({
    compiledRenderers,
    header: model.header,
    details: model.details,
    footer: model.footer,
    componentCss: model.componentCss,
    initialUpdatePayload: model.updatePayload,
    voided: payload.voided === true,
  })
  const browser = await getBrowser()
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 } })
  const events: unknown[] = []
  await page.exposeFunction("__reportRendererEvent", (event: unknown) => {
    events.push(event)
  })
  await page.addInitScript(() => {
    const originalPostMessage = window.postMessage.bind(window) as (
      message: unknown,
      ...args: unknown[]
    ) => void
    window.postMessage = ((message: unknown, ...args: unknown[]) => {
      void (
        window as unknown as {
          __reportRendererEvent?: (payload: unknown) => Promise<void>
        }
      ).__reportRendererEvent?.(message)
      return originalPostMessage(message, ...args)
    }) as typeof window.postMessage
    window.addEventListener("message", (event) => {
      void (
        window as unknown as {
          __reportRendererEvent?: (payload: unknown) => Promise<void>
        }
      ).__reportRendererEvent?.(event.data)
    })
  })
  await page.route("**/*", async (route) => {
    const requestUrl = new URL(route.request().url())
    if (
      ["localhost", "127.0.0.1"].includes(requestUrl.hostname) &&
      requestUrl.port === "9000"
    ) {
      requestUrl.hostname = "minio"
      await route.continue({ url: requestUrl.toString() })
      return
    }
    await route.continue()
  })
  try {
    await page.setContent(html, { waitUntil: "load" })
    await page.waitForSelector("#report-main", { timeout: 10_000 })
    await page.evaluate((updatePayload) => {
      window.postMessage(
        {
          type: "report-document-update-config",
          payload: updatePayload,
        },
        "*",
      )
    }, model.updatePayload)
    await page.waitForFunction(
      () => Number(document.querySelector("#report-main")?.children.length) > 0,
      null,
      { timeout: 10_000 },
    )
    const runtimeError = events.find(
      (item) =>
        item &&
        typeof item === "object" &&
        (item as { type?: unknown }).type === "report-document-error",
    )
    if (runtimeError) {
      throw new Error(
        String(
          (runtimeError as { message?: unknown }).message ||
            "Le rendu du rapport a échoué",
        ),
      )
    }
    await page.emulateMedia({ media: "print" })
    await page.addStyleTag({
      content: "@page { size: A4 portrait; margin: 14mm; }",
    })
    return await page.pdf({
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    })
  } finally {
    await page.close()
  }
}

Bun.serve({
  hostname: "0.0.0.0",
  port: Number(process.env.REPORT_RENDERER_PORT || "3100"),
  async fetch(request) {
    const url = new URL(request.url)
    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse(200, { status: "ok" })
    }
    if (request.method !== "POST" || url.pathname !== "/render") {
      return jsonResponse(404, { detail: "Not found" })
    }
    try {
      const payload = (await request.json()) as RenderReportRequest
      const pdf = await renderReportPdf(payload)
      return new Response(new Uint8Array(pdf), {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Cache-Control": "no-store",
        },
      })
    } catch (error) {
      return jsonResponse(422, {
        detail:
          error instanceof Error
            ? error.message
            : "Le rendu du rapport a échoué",
      })
    }
  },
})
