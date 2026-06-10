import type { ColumnDef } from "@tanstack/react-table"

import type { InsurancePricingDetailPublic } from "@/client"
import { formatPrice } from "@/lib/format"
import { InsurancePricingActionsMenu } from "./InsurancePricingActionsMenu"

export function getInsurancePricingColumns(
  onDeleted: () => void,
): ColumnDef<InsurancePricingDetailPublic>[] {
  return [
    {
      id: "provider_name",
      header: "Assureur",
      cell: ({ row }) => (
        <span className="font-medium">
          {row.original.insurance_provider_name}
        </span>
      ),
    },
    {
      id: "catalog_code",
      header: "Code",
      cell: ({ row }) => (
        <span className="font-mono text-xs">{row.original.catalog_code}</span>
      ),
    },
    {
      id: "catalog_name",
      header: "Test",
      cell: ({ row }) => (
        <div className="min-w-0">
          <div className="truncate font-medium">
            {row.original.catalog_name}
          </div>
          <div className="text-xs text-muted-foreground">
            Catalogue : {formatPrice(row.original.catalog_price)}
          </div>
        </div>
      ),
    },
    {
      id: "catalog_price",
      header: "Prix catalogue",
      cell: ({ row }) => formatPrice(row.original.catalog_price),
    },
    {
      id: "insurance_price",
      header: "Prix assurance",
      cell: ({ row }) => (
        <span className="font-medium">
          {formatPrice(row.original.insurance_price)}
        </span>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <InsurancePricingActionsMenu
            pricing={row.original}
            onDeleted={onDeleted}
          />
        </div>
      ),
    },
  ]
}
