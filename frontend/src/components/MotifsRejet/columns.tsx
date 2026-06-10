import type { ColumnDef } from "@tanstack/react-table"
import type { RejectionReasonPublic } from "@/client"
import { MotifRejetActionsMenu } from "./MotifRejetActionsMenu"

export const columns: ColumnDef<RejectionReasonPublic>[] = [
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
        <MotifRejetActionsMenu item={row.original} />
      </div>
    ),
  },
]
