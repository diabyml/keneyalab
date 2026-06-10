import type { InvoiceListItemPublic, PaymentStatus } from "@/client"
import type { ExportColumn } from "@/components/Common/tableExport"
import { formatDateTime, formatMoney } from "@/components/Orders/utils"

export const INVOICE_STATUS_LABELS: Record<PaymentStatus, string> = {
  unpaid: "Non payée",
  partial: "Partiellement payée",
  paid: "Payée",
  refunded: "Remboursée",
}

export function invoiceExportColumns(): ExportColumn<InvoiceListItemPublic>[] {
  return [
    {
      header: "Facture",
      value: (row) => `${row.invoice_number} v${row.version}`,
    },
    { header: "Demande", value: (row) => row.accession_number },
    { header: "Patient", value: (row) => row.patient_name },
    { header: "Identifiant patient", value: (row) => row.patient_identifier },
    {
      header: "Assurance",
      value: (row) => row.insurance_provider_name ?? "",
    },
    { header: "Net", value: (row) => formatMoney(row.net_amount) },
    { header: "Payé", value: (row) => formatMoney(row.amount_paid) },
    { header: "Solde", value: (row) => formatMoney(row.balance_due) },
    {
      header: "Statut",
      value: (row) => INVOICE_STATUS_LABELS[row.payment_status],
    },
    { header: "Créée le", value: (row) => formatDateTime(row.created_at) },
  ]
}
