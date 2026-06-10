import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"

import type { InvoiceListItemPublic, PaymentStatus } from "@/client"
import { formatDateTime, formatMoney } from "@/components/Orders/utils"
import { Badge } from "@/components/ui/badge"
import { InvoiceActionsMenu } from "./InvoiceActionsMenu"
import { INVOICE_STATUS_LABELS } from "./utils"

const helper = createColumnHelper<InvoiceListItemPublic>()

export const invoiceColumns: ColumnDef<InvoiceListItemPublic, any>[] = [
  helper.accessor("invoice_number", {
    header: "Facture",
    cell: ({ row }) => (
      <Link
        to="/invoices/$invoiceId"
        params={{ invoiceId: row.original.id }}
        className="block"
      >
        <div className="font-mono text-sm font-medium text-primary hover:underline">
          {row.original.invoice_number}
        </div>
        <div className="text-xs text-muted-foreground">
          Version {row.original.version}
          {row.original.is_voided ? " · Annulée" : ""}
        </div>
      </Link>
    ),
  }),
  helper.accessor("patient_name", {
    header: "Patient",
    cell: ({ row }) => (
      <Link
        to="/patients/$patientId"
        params={{ patientId: row.original.patient_id }}
        className="block"
      >
        <div className="font-medium text-primary hover:underline">
          {row.original.patient_name}
        </div>
        <div className="text-xs text-muted-foreground">
          {row.original.patient_identifier}
        </div>
      </Link>
    ),
  }),
  helper.accessor("accession_number", {
    header: "Demande",
    cell: ({ row }) => (
      <Link
        to="/orders/$orderId"
        params={{ orderId: row.original.order_id }}
        className="font-mono text-xs text-primary hover:underline"
      >
        {row.original.accession_number}
      </Link>
    ),
  }),
  helper.accessor("insurance_provider_name", {
    header: "Assurance",
    cell: ({ getValue }) => getValue() ?? "Paiement direct",
  }),
  helper.accessor("net_amount", {
    header: "Net",
    cell: ({ getValue }) => (
      <span className="tabular-nums">{formatMoney(getValue())}</span>
    ),
  }),
  helper.accessor("balance_due", {
    header: "Solde",
    cell: ({ getValue }) => (
      <span className="tabular-nums font-medium">
        {formatMoney(getValue())}
      </span>
    ),
  }),
  helper.accessor("payment_status", {
    header: "Statut",
    cell: ({ getValue }) => (
      <Badge variant="outline">
        {INVOICE_STATUS_LABELS[getValue() as PaymentStatus]}
      </Badge>
    ),
  }),
  helper.accessor("created_at", {
    header: "Créée le",
    cell: ({ getValue }) => formatDateTime(getValue()),
  }),
  helper.display({
    id: "actions",
    header: "",
    cell: ({ row }) => <InvoiceActionsMenu invoice={row.original} />,
  }),
]
