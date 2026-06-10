import type { ColumnDef } from "@tanstack/react-table"

import type { TitlePublic } from "@/client"
import { TitreActionsMenu } from "./TitreActionsMenu"

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

export const columns: ColumnDef<TitlePublic>[] = [
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
        <TitreActionsMenu title={row.original} />
      </div>
    ),
  },
]
