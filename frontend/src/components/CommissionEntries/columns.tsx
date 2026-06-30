import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"
import { Eye } from "lucide-react"

import type {
  DoctorCommissionEntryListItemPublic,
  PayoutStatus,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatDateTime, formatMoney, PAYOUT_STATUS_LABELS } from "./utils"

const helper = createColumnHelper<DoctorCommissionEntryListItemPublic>()

export function getCommissionEntryColumns(
  onOpen: (id: string) => void,
): ColumnDef<DoctorCommissionEntryListItemPublic, any>[] {
  return [
    helper.accessor("accession_number", {
      header: "Demande",
      cell: ({ row }) => (
        <div>
          <Link
            to="/orders/$orderId"
            params={{ orderId: row.original.order_id }}
            className="font-mono font-medium text-primary hover:underline"
          >
            {row.original.accession_number}
          </Link>
          <div className="text-xs text-muted-foreground">
            {row.original.invoice_number}
          </div>
        </div>
      ),
    }),
    helper.accessor("doctor_name", {
      header: "Médecin",
      cell: ({ getValue }) => <span className="font-medium">{getValue()}</span>,
    }),
    helper.accessor("patient_name", {
      header: "Patient",
      cell: ({ row }) => (
        <Link
          to="/patients/$patientId"
          params={{ patientId: row.original.patient_id }}
          className="hover:text-primary hover:underline"
        >
          {row.original.patient_name}
        </Link>
      ),
    }),
    helper.accessor("commission_amount", {
      header: "Commission",
      cell: ({ getValue }) => (
        <span className="text-xs tabular-nums">{formatMoney(getValue())}</span>
      ),
    }),
    helper.accessor("total_adjustments", {
      header: "Ajustements",
      cell: ({ row }) => (
        <div className="text-right text-xs tabular-nums">
          <div>{formatMoney(row.original.total_adjustments)}</div>
          <div className="text-xs text-muted-foreground">
            {row.original.adjustment_count} écriture
            {row.original.adjustment_count !== 1 && "s"}
          </div>
        </div>
      ),
    }),
    helper.accessor("outstanding_amount", {
      header: "Solde ouvert",
      cell: ({ getValue }) => (
        <span className="text-xs font-medium tabular-nums">
          {formatMoney(getValue())}
        </span>
      ),
    }),
    helper.accessor("payout_status", {
      header: "Statut",
      cell: ({ getValue }) => {
        const status = getValue() as PayoutStatus
        return (
          <Badge variant={status === "paid" ? "secondary" : "outline"}>
            {PAYOUT_STATUS_LABELS[status]}
          </Badge>
        )
      },
    }),
    helper.accessor("created_at", {
      header: "Créée le",
      cell: ({ getValue }) => formatDateTime(getValue()),
    }),
    helper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpen(row.original.id)}
            aria-label="Voir le détail de l'écriture"
          >
            <Eye className="size-4" />
          </Button>
        </div>
      ),
    }),
  ]
}
