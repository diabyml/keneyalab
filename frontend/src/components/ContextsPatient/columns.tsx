import type { ColumnDef } from "@tanstack/react-table"
import type { PatientContextPublic } from "@/client"
import { ContextPatientActionsMenu } from "./ContextPatientActionsMenu"

export const columns: ColumnDef<PatientContextPublic>[] = [
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
        <ContextPatientActionsMenu item={row.original} />
      </div>
    ),
  },
]
