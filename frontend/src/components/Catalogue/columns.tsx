import type { ColumnDef } from "@tanstack/react-table"
import { Eye } from "lucide-react"

import type { CatalogSummaryPublic } from "@/client"
import type { ExportColumn } from "@/components/Common/tableExport"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatPrice } from "@/lib/format"
import { CatalogTypeBadge } from "./CatalogTypeBadge"
import { catalogTypeLabel, rowCountLabel } from "./utils"

export function getCatalogColumns(
  onSelect: (id: string) => void,
): ColumnDef<CatalogSummaryPublic>[] {
  return [
    {
      accessorKey: "code",
      header: "Code",
      cell: ({ row }) => (
        <span className="font-medium">{row.original.code}</span>
      ),
    },
    { accessorKey: "name", header: "Nom" },
    {
      accessorKey: "type",
      header: "Type",
      cell: ({ row }) => <CatalogTypeBadge type={row.original.type} />,
    },
    {
      accessorKey: "category_name",
      header: "Catégorie",
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.category_name ?? "Non classé"}
        </span>
      ),
    },
    {
      accessorKey: "price",
      header: "Prix",
      cell: ({ row }) => (
        <span className="block text-right">
          {formatPrice(row.original.price)}
        </span>
      ),
    },
    {
      id: "content",
      header: "Contenu",
      cell: ({ row }) =>
        row.original.type === "item"
          ? `${rowCountLabel(row.original.analytes_count ?? 0, "analyte", "analytes")} · ${rowCountLabel(
              row.original.specimen_requirements_count ?? 0,
              "prélèvement",
              "prélèvements",
            )}`
          : rowCountLabel(row.original.panel_items_count ?? 0, "test", "tests"),
    },
    {
      accessorKey: "is_orderable",
      header: "Statut",
      cell: ({ row }) => (
        <Badge variant={row.original.is_deleted ? "outline" : "secondary"}>
          {row.original.is_deleted
            ? "Supprimé"
            : row.original.is_orderable
              ? "Commandable"
              : "Masqué"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => onSelect(row.original.id)}
          >
            <Eye className="size-4" />
            <span className="sr-only">Afficher {row.original.name}</span>
          </Button>
        </div>
      ),
    },
  ]
}

export const catalogExportColumns: ExportColumn<CatalogSummaryPublic>[] = [
  { header: "Code", value: (row) => row.code },
  { header: "Nom", value: (row) => row.name },
  { header: "Type", value: (row) => catalogTypeLabel(row.type) },
  { header: "Catégorie", value: (row) => row.category_name ?? "" },
  { header: "Prix", value: (row) => formatPrice(row.price) },
  {
    header: "Statut",
    value: (row) =>
      row.is_deleted ? "Supprimé" : row.is_orderable ? "Commandable" : "Masqué",
  },
]
