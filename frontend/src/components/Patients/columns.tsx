import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"

import type { PatientPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { PatientActionsMenu } from "./PatientActionsMenu"
import {
  formatDate,
  GENDER_LABELS,
  getPatientAge,
  getPatientName,
} from "./utils"

export function getPatientColumns(
  onRestored: () => void,
): ColumnDef<PatientPublic>[] {
  return [
    {
      id: "identifier",
      accessorKey: "identifier",
      header: "Identifiant",
      cell: ({ row }) => (
        <Link
          to="/patients/$patientId"
          params={{ patientId: row.original.id }}
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          {row.original.identifier}
        </Link>
      ),
    },
    {
      id: "last_name",
      header: "Patient",
      cell: ({ row }) => (
        <div className="min-w-0">
          <div className="truncate font-medium">
            {getPatientName(row.original)}
          </div>
          <div className="text-xs text-muted-foreground">
            {GENDER_LABELS[row.original.gender]}
          </div>
        </div>
      ),
    },
    {
      id: "date_of_birth",
      accessorKey: "date_of_birth",
      header: "Naissance",
      cell: ({ row }) => (
        <div>
          <div>{formatDate(row.original.date_of_birth)}</div>
          <div className="text-xs text-muted-foreground">
            {getPatientAge(row.original.date_of_birth)} ans
          </div>
        </div>
      ),
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
          <PatientActionsMenu patient={row.original} onRestored={onRestored} />
        </div>
      ),
    },
  ]
}
