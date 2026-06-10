import type { RuleSeverity, TriggerOperator } from "@/client"

export const SEVERITY_LABELS: Record<RuleSeverity, string> = {
  warning: "Avertissement",
  error: "Erreur",
}

export const OPERATOR_LABELS: Record<TriggerOperator, string> = {
  gt: ">",
  gte: ">=",
  lt: "<",
  lte: "<=",
  eq: "=",
  in: "dans",
}

export const STATUS_OPTIONS = [
  { value: "active", label: "Actives" },
  { value: "deleted", label: "Supprimées" },
  { value: "all", label: "Toutes" },
] as const

export const SEVERITY_OPTIONS = [
  { value: "all", label: "Toutes" },
  { value: "warning", label: "Avertissement" },
  { value: "error", label: "Erreur" },
] as const

export const OPERATOR_OPTIONS = [
  { value: "all", label: "Tous" },
  { value: "gt", label: ">" },
  { value: "gte", label: ">=" },
  { value: "lt", label: "<" },
  { value: "lte", label: "<=" },
  { value: "eq", label: "=" },
  { value: "in", label: "dans" },
] as const
