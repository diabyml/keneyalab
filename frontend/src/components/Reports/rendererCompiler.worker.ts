import * as esbuild from "esbuild-wasm"
import wasmUrl from "esbuild-wasm/esbuild.wasm?url"

let initialized: Promise<void> | null = null

function initialize() {
  initialized ??= esbuild.initialize({ wasmURL: wasmUrl, worker: false })
  return initialized
}

self.onmessage = async (
  event: MessageEvent<{ id: string; source: string }>,
) => {
  const { id, source } = event.data
  try {
    await initialize()
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
    self.postMessage({ id, code: result.code })
  } catch (error) {
    self.postMessage({
      id,
      error: error instanceof Error ? error.message : "Compilation impossible",
    })
  }
}
