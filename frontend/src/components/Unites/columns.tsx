import type { ColumnDef } from "@tanstack/react-table"

import type { UnitPublic } from "@/client"
import { UniteActionsMenu } from "./UniteActionsMenu"

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

export const columns: ColumnDef<UnitPublic>[] = [
  {
    accessorKey: "name",
    header: "Nom",
    cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
  },
  {
    accessorKey: "created_at",
    header: "Créé le",
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {formatDate(row.original.created_at)}
      </span>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <UniteActionsMenu unit={row.original} />
      </div>
    ),
  },
]
