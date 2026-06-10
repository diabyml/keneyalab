import type { CatalogType, SortOrder } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"

export const ALL = "__all__"
export const NONE = "__none__"

export type StatusFilter = "active" | "deleted" | "all"
export type OrderableFilter = "all" | "yes" | "no"
export type SortBy = "code" | "name" | "type" | "price" | "is_orderable"

export interface CatalogFormState {
  type: CatalogType
  code: string
  name: string
  price: string
  categoryId: string
  categoryLabel: string
  isOrderable: boolean
}

export interface SpecimenFormState {
  specimenTypeId: string
  volumeMl: string
  instructions: string
}

export interface CatalogFilterState {
  statusFilter: StatusFilter
  typeFilter: string
  categoryFilter: string
  categoryFilterOption: SearchSelectOption | null
  orderableFilter: OrderableFilter
}

export interface CatalogQueryParams extends CatalogFilterState {
  page: number
  pageSize: number
  search: string
  sortBy: SortBy
  sortOrder: SortOrder
}
