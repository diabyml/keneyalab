import type { ColumnDef } from "@tanstack/react-table"
import type { InsuranceProviderPublic } from "@/client"
import { AssureurActionsMenu } from "./AssureurActionsMenu"

export function getAssureurColumns(
  onRestored: () => void,
): ColumnDef<InsuranceProviderPublic>[] {
  return [
    {
      id: "name",
      accessorKey: "name",
      header: "Nom",
      cell: ({ row }) => (
        <span className="font-medium">{row.original.name}</span>
      ),
    },
    {
      id: "status",
      header: "Statut",
      cell: ({ row }) => (row.original.is_deleted ? "Supprimé" : "Actif"),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <AssureurActionsMenu item={row.original} onRestored={onRestored} />
        </div>
      ),
    },
  ]
}

export function assureurExportColumns() {
  return [
    { header: "Nom", value: (row: InsuranceProviderPublic) => row.name },
    {
      header: "Statut",
      value: (row: InsuranceProviderPublic) =>
        row.is_deleted ? "Supprimé" : "Actif",
    },
  ]
}
