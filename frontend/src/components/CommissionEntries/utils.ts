import type { PayoutStatus } from "@/client"

export const PAYOUT_STATUS_LABELS: Record<PayoutStatus, string> = {
  pending: "En attente",
  paid: "Payée",
}

export function formatMoney(value: string | number) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

export function formatRate(value: string | number | undefined) {
  return new Intl.NumberFormat("fr-FR", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value ?? 0))
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "—"
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value))
}
