import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"

import type { DoctorWithTitlePublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { DoctorActionsMenu } from "./DoctorActionsMenu"
import { getDoctorName } from "./utils"

export function getDoctorColumns(
  onRestored: () => void,
): ColumnDef<DoctorWithTitlePublic>[] {
  return [
    {
      id: "last_name",
      header: "Médecin",
      cell: ({ row }) => (
        <div className="min-w-0">
          <Link
            to="/doctors/$doctorId"
            params={{ doctorId: row.original.id }}
            className="truncate font-medium text-primary underline-offset-4 hover:underline"
          >
            {getDoctorName(row.original)}
          </Link>
          <div className="text-xs text-muted-foreground">
            {row.original.title_name ?? "Sans titre"}
          </div>
        </div>
      ),
    },
    {
      id: "provenance",
      accessorKey: "provenance",
      header: "Provenance",
      cell: ({ row }) => row.original.provenance ?? "-",
    },
    {
      id: "phone",
      accessorKey: "phone",
      header: "Téléphone",
      cell: ({ row }) => row.original.phone ?? "-",
    },
    {
      id: "status",
      header: "Statut",
      cell: ({ row }) =>
        row.original.is_deleted ? (
          <Badge variant="destructive">Supprimé</Badge>
        ) : (
          <Badge variant="secondary">Actif</Badge>
        ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <DoctorActionsMenu doctor={row.original} onRestored={onRestored} />
        </div>
      ),
    },
  ]
}
