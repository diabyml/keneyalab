import type { AnalyteDataType } from "@/client"

export const DATA_TYPE_LABELS: Record<AnalyteDataType, string> = {
  numeric: "Numérique",
  text: "Texte",
  options: "Options",
  image: "Image",
}

export const DATA_TYPE_OPTIONS: AnalyteDataType[] = [
  "numeric",
  "text",
  "options",
  "image",
]
