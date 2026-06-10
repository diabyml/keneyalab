import type { InsurancePricingDetailPublic } from "@/client"
import { formatPrice } from "@/lib/format"

export type InsurancePricingSortBy =
  | "provider_name"
  | "catalog_code"
  | "catalog_name"
  | "catalog_price"
  | "insurance_price"
  | "created_at"

export function pricingExportColumns() {
  return [
    {
      header: "Assureur",
      value: (row: InsurancePricingDetailPublic) => row.insurance_provider_name,
    },
    {
      header: "Code test",
      value: (row: InsurancePricingDetailPublic) => row.catalog_code,
    },
    {
      header: "Test",
      value: (row: InsurancePricingDetailPublic) => row.catalog_name,
    },
    {
      header: "Prix catalogue",
      value: (row: InsurancePricingDetailPublic) =>
        formatPrice(row.catalog_price),
    },
    {
      header: "Prix assurance",
      value: (row: InsurancePricingDetailPublic) =>
        formatPrice(row.insurance_price),
    },
  ]
}
