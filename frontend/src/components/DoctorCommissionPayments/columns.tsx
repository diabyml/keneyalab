import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"
import type { DoctorCommissionPaymentListItemPublic } from "@/client"
import { formatDateTime, formatMoney } from "./utils"

const helper = createColumnHelper<DoctorCommissionPaymentListItemPublic>()

export const paymentColumns: ColumnDef<
  DoctorCommissionPaymentListItemPublic,
  any
>[] = [
  helper.accessor("created_at", {
    header: "Date",
    cell: ({ getValue }) => formatDateTime(getValue()),
  }),
  helper.accessor("doctor_name", {
    header: "Médecin",
    cell: ({ row }) => (
      <Link
        to="/commissions/payments/$paymentId"
        params={{ paymentId: row.original.id }}
        className="font-medium text-primary hover:underline"
      >
        {row.original.doctor_name}
      </Link>
    ),
  }),
  helper.accessor("payment_method_name", { header: "Méthode" }),
  helper.accessor("reference", {
    header: "Référence",
    cell: ({ getValue }) => getValue() || "—",
  }),
  helper.accessor("line_count", { header: "Lignes" }),
  helper.accessor("total_commission_amount", {
    header: "Total",
    cell: ({ getValue }) => (
      <span className="font-medium tabular-nums">
        {formatMoney(getValue())}
      </span>
    ),
  }),
  helper.accessor("created_by_name", {
    header: "Opérateur",
    cell: ({ getValue }) => getValue() || "—",
  }),
]
