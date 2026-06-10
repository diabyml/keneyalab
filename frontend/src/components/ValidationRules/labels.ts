import type { AnalyteDataType, TargetGenderType } from "@/client"

export const DATA_TYPE_LABELS: Record<AnalyteDataType, string> = {
  numeric: "Numérique",
  text: "Texte",
  options: "Options",
  image: "Image",
}

export const TARGET_GENDER_LABELS: Record<TargetGenderType, string> = {
  all: "Tous",
  male: "Homme",
  female: "Femme",
}
