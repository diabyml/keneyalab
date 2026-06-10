import type { ColumnDef } from "@tanstack/react-table"
import type { PaymentMethodPublic } from "@/client"
import { MethodePaiementActionsMenu } from "./MethodePaiementActionsMenu"

export const columns: ColumnDef<PaymentMethodPublic>[] = [
  {
    accessorKey: "name",
    header: "Nom",
    cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <MethodePaiementActionsMenu item={row.original} />
      </div>
    ),
  },
]
