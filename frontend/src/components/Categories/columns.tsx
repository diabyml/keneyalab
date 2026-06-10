import type { ColumnDef } from "@tanstack/react-table"

import type { CategoryPublic } from "@/client"
import { CategoryActionsMenu } from "./CategoryActionsMenu"

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

export const columns: ColumnDef<CategoryPublic>[] = [
  {
    accessorKey: "sort_order",
    header: "Ordre",
    cell: ({ row }) => (
      <span className="text-muted-foreground tabular-nums">
        {row.original.sort_order}
      </span>
    ),
  },
  {
    accessorKey: "name",
    header: "Nom",
    cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
  },
  {
    accessorKey: "created_at",
    header: "Créée le",
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
        <CategoryActionsMenu category={row.original} />
      </div>
    ),
  },
]
