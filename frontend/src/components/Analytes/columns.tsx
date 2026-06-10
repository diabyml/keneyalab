import type { ColumnDef } from "@tanstack/react-table"

import type { AnalytePublic } from "@/client"
import { HtmlContent } from "@/components/Common/HtmlContent"
import { Badge } from "@/components/ui/badge"
import { AnalyteActionsMenu } from "./AnalyteActionsMenu"
import { DATA_TYPE_LABELS } from "./labels"

export function getColumns(
  unitsById: Map<string, string>,
): ColumnDef<AnalytePublic>[] {
  return [
    {
      accessorKey: "code",
      header: "Code",
      cell: ({ row }) => (
        <span className="font-mono text-sm font-medium">
          {row.original.code}
        </span>
      ),
    },
    {
      accessorKey: "name",
      header: "Nom",
      cell: ({ row }) => (
        <span className="font-medium">{row.original.name}</span>
      ),
    },
    {
      accessorKey: "data_type",
      header: "Type",
      cell: ({ row }) => DATA_TYPE_LABELS[row.original.data_type],
    },
    {
      accessorKey: "unit_id",
      header: "Unité",
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.unit_id
            ? (unitsById.get(row.original.unit_id) ?? "—")
            : "—"}
        </span>
      ),
    },
    {
      accessorKey: "is_calculated",
      header: "Calculé",
      cell: ({ row }) =>
        row.original.is_calculated ? (
          <Badge variant="secondary">Oui</Badge>
        ) : (
          <span className="text-muted-foreground">Non</span>
        ),
    },
    {
      accessorKey: "reference_text",
      header: "Référence",
      cell: ({ row }) => (
        <HtmlContent
          html={row.original.reference_text}
          className="line-clamp-2 max-w-sm text-muted-foreground"
        />
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <AnalyteActionsMenu analyte={row.original} />
        </div>
      ),
    },
  ]
}
