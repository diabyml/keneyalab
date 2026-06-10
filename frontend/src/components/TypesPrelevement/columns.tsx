import type { ColumnDef } from "@tanstack/react-table"
import type { SpecimenTypePublic } from "@/client"
import { TypePrelevementActionsMenu } from "./TypePrelevementActionsMenu"

export const columns: ColumnDef<SpecimenTypePublic>[] = [
  {
    accessorKey: "name",
    header: "Nom",
    cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const d = row.original.description
      return (
        <span className="max-w-xs truncate block text-muted-foreground">
          {d || "—"}
        </span>
      )
    },
  },
  {
    accessorKey: "color",
    header: "Couleur",
    cell: ({ row }) => {
      const c = row.original.color
      if (!c) return <span className="text-muted-foreground">—</span>
      return (
        <div className="flex items-center gap-2">
          <div
            className="size-4 rounded-full border"
            style={{ backgroundColor: c }}
          />
          <span className="text-xs font-mono text-muted-foreground">{c}</span>
        </div>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <TypePrelevementActionsMenu item={row.original} />
      </div>
    ),
  },
]
