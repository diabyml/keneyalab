export type ReportAnalyte = {
  analyte_id: string
  analyte_code: string
  analyte_name: string
  data_type: string
  unit_name?: string | null
  reference_text?: string | null
  result_value?: string | null
  image_url?: string | null
  status: string
  is_abnormal?: boolean
  is_critical?: boolean
  verified_by_name?: string | null
  verified_at?: string | null
  comments?: Array<{ id?: string; comment: string; user_name?: string | null }>
}

export type ReportTest = {
  order_item_id: string
  catalog_code: string
  catalog_name: string
  analytes: ReportAnalyte[]
}

export type ReportCategory = {
  id?: string | null
  name: string
  tests: ReportTest[]
}

export type ReportSnapshot = {
  order: {
    id?: string | null
    accession_number: string
    status: string
    revision_number: number
  }
  patient: {
    id?: string | null
    identifier: string
    name: string
    date_of_birth: string
    age: number
    gender: string
    gender_label: string
    context?: string | null
    phone?: string | null
    address?: string | null
  }
  doctor: {
    name: string
    title?: string | null
    provenance?: string | null
    phone?: string | null
  }
  lab: Record<string, unknown>
  categories: ReportCategory[]
  totals: { results: number; verified: number }
}

export type ReportRenderConfig = {
  category_order: string[]
  category_page_breaks: Record<string, boolean>
  hidden_analyte_ids: string[]
}

export type ComponentTemplate = {
  id: string
  name: string
  version_id: string
  version: number
  html_source: string
  css_source: string
}

export type RendererTemplate = {
  id: string
  name: string
  version_id: string
  version: number
  jsx_source: string
  css_source: string
}

export type ReportTemplateSnapshot = {
  header: ComponentTemplate
  details: ComponentTemplate
  footer: ComponentTemplate
  renderers: Record<string, RendererTemplate>
}

export function asReportSnapshot(value: unknown): ReportSnapshot {
  return value as ReportSnapshot
}

export function asTemplateSnapshot(value: unknown): ReportTemplateSnapshot {
  return value as ReportTemplateSnapshot
}

export function reportCategoryKey(category: ReportCategory) {
  return category.id ?? "uncategorized"
}

export function defaultReportRenderConfig(): ReportRenderConfig {
  return {
    category_order: [],
    category_page_breaks: {},
    hidden_analyte_ids: [],
  }
}

export function normalizeReportRenderConfig(
  value: Partial<ReportRenderConfig> | null | undefined,
): ReportRenderConfig {
  return {
    category_order: [...(value?.category_order ?? [])],
    category_page_breaks: { ...(value?.category_page_breaks ?? {}) },
    hidden_analyte_ids: [...(value?.hidden_analyte_ids ?? [])],
  }
}

export function applyReportRenderConfig(
  snapshot: ReportSnapshot,
  value: Partial<ReportRenderConfig> | null | undefined,
): ReportSnapshot {
  const config = normalizeReportRenderConfig(value)
  const hidden = new Set(config.hidden_analyte_ids)
  const categoriesByKey = new Map(
    snapshot.categories.map((category) => [
      reportCategoryKey(category),
      category,
    ]),
  )
  const orderedKeys = [
    ...config.category_order.filter((key) => categoriesByKey.has(key)),
    ...snapshot.categories
      .map(reportCategoryKey)
      .filter((key) => !config.category_order.includes(key)),
  ]

  return {
    ...snapshot,
    categories: orderedKeys
      .map((key) => categoriesByKey.get(key))
      .filter((category): category is ReportCategory => Boolean(category))
      .map((category) => ({
        ...category,
        tests: category.tests
          .map((test) => ({
            ...test,
            analytes: test.analytes.filter(
              (analyte) => !hidden.has(analyte.analyte_id),
            ),
          }))
          .filter((test) => test.analytes.length > 0),
      }))
      .filter((category) => category.tests.length > 0),
  }
}
