import type { CatalogType } from "@/client"
import { type CatalogFormState, type CatalogQueryParams, NONE } from "./types"

export function emptyCatalogForm(type: CatalogType = "item"): CatalogFormState {
  return {
    type,
    code: "",
    name: "",
    price: "0.00",
    categoryId: NONE,
    categoryLabel: "",
    isOrderable: true,
  }
}

export function catalogTypeLabel(type: CatalogType) {
  return type === "item" ? "Test" : "Panel"
}

export function rowCountLabel(count: number, singular: string, plural: string) {
  return `${count} ${count > 1 ? plural : singular}`
}

export function buildCatalogRequest(form: CatalogFormState) {
  const body = {
    type: form.type,
    code: form.code.trim().toUpperCase(),
    name: form.name.trim(),
    category_id: form.categoryId === NONE ? null : form.categoryId,
    is_orderable: form.isOrderable,
  }
  if (form.type === "item") {
    return { ...body, price: form.price.trim() || "0" }
  }
  return body
}

export function buildCatalogUpdateRequest(form: CatalogFormState) {
  const body = buildCatalogRequest(form)
  const updateBody = {
    code: body.code,
    name: body.name,
    category_id: body.category_id,
    is_orderable: body.is_orderable,
  }
  if (form.type === "item" && "price" in body) {
    return { ...updateBody, price: body.price }
  }
  return updateBody
}

export function swapOrder<T extends { id: string; sort_order?: number }>(
  rows: T[],
  index: number,
  direction: -1 | 1,
) {
  const target = index + direction
  if (target < 0 || target >= rows.length) return null
  const next = rows.map((row, i) => ({ id: row.id, sort_order: i + 1 }))
  next[index] = { id: rows[target].id, sort_order: index + 1 }
  next[target] = { id: rows[index].id, sort_order: target + 1 }
  return next
}

export function getCatalogQueryKey(params: CatalogQueryParams) {
  return ["catalog", "list", params]
}

export function initialCatalogFilters() {
  return {
    statusFilter: "active" as const,
    typeFilter: "__all__",
    categoryFilter: "__all__",
    categoryFilterOption: null,
    orderableFilter: "all" as const,
  }
}
