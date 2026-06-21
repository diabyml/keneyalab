import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"

import type { OrderListItemPublic, OrderStatus, PaymentStatus } from "@/client"
import { OperationalId } from "@/components/Common/OperationalId"
import { StatusBadge } from "@/components/Common/StatusBadge"
import { OrderActionsMenu } from "./OrderActionsMenu"
import {
  formatDateTime,
  formatMoney,
  ORDER_STATUS_LABELS,
  PAYMENT_STATUS_LABELS,
} from "./utils"

const columnHelper = createColumnHelper<OrderListItemPublic>()

const orderTone: Record<
  OrderStatus,
  "pending" | "progress" | "success" | "warning" | "critical"
> = {
  registered: "pending",
  collected: "progress",
  in_progress: "progress",
  partial_results: "warning",
  completed: "success",
  cancelled: "critical",
}

const paymentTone: Record<
  PaymentStatus,
  "warning" | "progress" | "success" | "neutral"
> = {
  unpaid: "warning",
  partial: "progress",
  paid: "success",
  refunded: "neutral",
}

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
          className="hover:underline focus-visible:underline"
        >
          <OperationalId>{getValue()}</OperationalId>
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
        <StatusBadge tone={orderTone[getValue() as OrderStatus]}>
          {ORDER_STATUS_LABELS[getValue() as OrderStatus]}
        </StatusBadge>
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
      cell: ({ getValue }) => (
        <StatusBadge tone={paymentTone[getValue() as PaymentStatus]}>
          {PAYMENT_STATUS_LABELS[getValue() as PaymentStatus]}
        </StatusBadge>
      ),
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
