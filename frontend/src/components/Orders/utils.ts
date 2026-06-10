import type { OrderListItemPublic, OrderStatus, PaymentStatus } from "@/client"

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  registered: "Enregistrée",
  collected: "Prélevée",
  in_progress: "En cours",
  partial_results: "Résultats partiels",
  completed: "Terminée",
  cancelled: "Annulée",
}

export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  unpaid: "Impayée",
  partial: "Partielle",
  paid: "Payée",
  refunded: "Remboursée",
}

export function formatMoney(value: string | number) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "-"
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value))
}

export function orderExportColumns() {
  return [
    {
      header: "Demande",
      value: (row: OrderListItemPublic) => row.accession_number,
    },
    {
      header: "Patient",
      value: (row: OrderListItemPublic) => row.patient_name,
    },
    {
      header: "Identifiant patient",
      value: (row: OrderListItemPublic) => row.patient_identifier,
    },
    {
      header: "Médecin",
      value: (row: OrderListItemPublic) => row.doctor_name ?? "",
    },
    {
      header: "Statut",
      value: (row: OrderListItemPublic) => ORDER_STATUS_LABELS[row.status],
    },
    {
      header: "Montant net",
      value: (row: OrderListItemPublic) => Number(row.net_amount).toFixed(2),
    },
    {
      header: "Paiement",
      value: (row: OrderListItemPublic) =>
        PAYMENT_STATUS_LABELS[row.payment_status],
    },
    {
      header: "Créée le",
      value: (row: OrderListItemPublic) => formatDateTime(row.created_at),
    },
  ]
}
