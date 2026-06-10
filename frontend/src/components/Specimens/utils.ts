import type {
  PaymentStatus,
  SpecimenQueueItemPublic,
  SpecimenStatus,
} from "@/client"
import type { ExportColumn } from "@/components/Common/tableExport"
import { formatDateTime } from "@/components/Orders/utils"

export const SPECIMEN_STATUS_LABELS: Record<SpecimenStatus, string> = {
  pending: "À prélever",
  collected: "Prélevé",
  rejected: "Rejeté",
  processed: "Traité",
}

export const PAYMENT_LABELS: Record<PaymentStatus, string> = {
  unpaid: "Non payé",
  partial: "Partiel",
  paid: "Payé",
  refunded: "Remboursé",
}

export function specimenQueueExportColumns(): ExportColumn<SpecimenQueueItemPublic>[] {
  return [
    { header: "Demande", value: (row) => row.accession_number },
    { header: "Patient", value: (row) => row.patient_name },
    { header: "Identifiant", value: (row) => row.patient_identifier },
    { header: "Prélèvements", value: (row) => row.specimen_summary },
    { header: "En attente", value: (row) => row.pending_count },
    { header: "Prélevés", value: (row) => row.collected_count },
    { header: "Paiement", value: (row) => PAYMENT_LABELS[row.payment_status] },
    { header: "Créée le", value: (row) => formatDateTime(row.created_at) },
  ]
}

export function toLocalDateTimeInput(date = new Date()): string {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16)
}
