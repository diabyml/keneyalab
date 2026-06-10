import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"

import type { OrderListItemPublic, OrderStatus, PaymentStatus } from "@/client"
import { Badge } from "@/components/ui/badge"
import { OrderActionsMenu } from "./OrderActionsMenu"
import {
  formatDateTime,
  formatMoney,
  ORDER_STATUS_LABELS,
  PAYMENT_STATUS_LABELS,
} from "./utils"

const columnHelper = createColumnHelper<OrderListItemPublic>()

interface OrderColumnsOptions {
  showPatient?: boolean
  showDoctor?: boolean
}

export function getOrderColumns({
  showPatient = true,
  showDoctor = true,
}: OrderColumnsOptions = {}): ColumnDef<OrderListItemPublic, any>[] {
  return [
    columnHelper.accessor("accession_number", {
      header: "Demande",
      cell: ({ getValue, row }) => (
        <Link
          to="/orders/$orderId"
          params={{ orderId: row.original.id }}
          className="font-mono text-sm text-primary font-medium hover:underline focus-visible:underline"
        >
          {getValue()}
        </Link>
      ),
    }),
    ...(showPatient
      ? [
          columnHelper.accessor("patient_name", {
            header: "Patient",
            cell: ({ row }) => (
              <div>
                <div className="font-medium">{row.original.patient_name}</div>
                <div className="text-xs text-muted-foreground">
                  {row.original.patient_identifier}
                </div>
              </div>
            ),
          }),
        ]
      : []),
    ...(showDoctor
      ? [
          columnHelper.accessor("doctor_name", {
            header: "Médecin",
            cell: ({ getValue }) => getValue() ?? "Sans prescripteur",
          }),
        ]
      : []),
    columnHelper.accessor("status", {
      header: "Statut",
      cell: ({ getValue }) => (
        <Badge variant="outline">
          {ORDER_STATUS_LABELS[getValue() as OrderStatus]}
        </Badge>
      ),
    }),
    columnHelper.accessor("net_amount", {
      header: "Montant net",
      cell: ({ getValue }) => (
        <span className="tabular-nums">{formatMoney(getValue())}</span>
      ),
    }),
    columnHelper.accessor("payment_status", {
      header: "Paiement",
      cell: ({ getValue }) =>
        PAYMENT_STATUS_LABELS[getValue() as PaymentStatus],
    }),
    columnHelper.accessor("created_at", {
      header: "Créée le",
      cell: ({ getValue }) => formatDateTime(getValue()),
    }),
    columnHelper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => <OrderActionsMenu order={row.original} />,
    }),
  ]
}

export const orderColumns = getOrderColumns()
