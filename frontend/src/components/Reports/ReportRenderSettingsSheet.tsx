import {
  ArrowDown,
  ArrowUp,
  Eye,
  EyeOff,
  FileSymlink,
  GripVertical,
  RotateCcw,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import type {
  ReportCategory,
  ReportRenderConfig,
  ReportSnapshot,
} from "./reportTypes"
import {
  defaultReportRenderConfig,
  normalizeReportRenderConfig,
  reportCategoryKey,
} from "./reportTypes"

function moveItem<T>(items: T[], from: number, to: number) {
  if (to < 0 || to >= items.length) return items
  const next = [...items]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

function categoryAnalyteIds(category: ReportCategory) {
  return category.tests.flatMap((test) =>
    test.analytes.map((analyte) => analyte.analyte_id),
  )
}

function orderedCategories(
  snapshot: ReportSnapshot,
  config: ReportRenderConfig,
) {
  const byKey = new Map(
    snapshot.categories.map((category) => [
      reportCategoryKey(category),
      category,
    ]),
  )
  const keys = [
    ...config.category_order.filter((key) => byKey.has(key)),
    ...snapshot.categories
      .map(reportCategoryKey)
      .filter((key) => !config.category_order.includes(key)),
  ]
  return keys
    .map((key) => byKey.get(key))
    .filter((category): category is ReportCategory => Boolean(category))
}

export function ReportRenderSettingsSheet({
  open,
  onOpenChange,
  snapshot,
  value,
  onChange,
  readOnly = false,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  snapshot: ReportSnapshot
  value: Partial<ReportRenderConfig> | null | undefined
  onChange: (value: ReportRenderConfig) => void
  readOnly?: boolean
}) {
  const config = useMemo(() => normalizeReportRenderConfig(value), [value])
  const categories = useMemo(
    () => orderedCategories(snapshot, config),
    [snapshot, config],
  )
  const [draggedKey, setDraggedKey] = useState<string | null>(null)

  useEffect(() => {
    setDraggedKey(null)
  }, [])

  const update = (next: ReportRenderConfig) => {
    if (!readOnly) onChange(next)
  }

  const setCategoryOrder = (categoriesInOrder: ReportCategory[]) => {
    update({
      ...config,
      category_order: categoriesInOrder.map(reportCategoryKey),
    })
  }

  const moveCategory = (from: number, to: number) => {
    setCategoryOrder(moveItem(categories, from, to))
  }

  const handleDrop = (targetKey: string) => {
    if (!draggedKey || draggedKey === targetKey || readOnly) return
    const from = categories.findIndex(
      (category) => reportCategoryKey(category) === draggedKey,
    )
    const to = categories.findIndex(
      (category) => reportCategoryKey(category) === targetKey,
    )
    if (from === -1 || to === -1) return
    setCategoryOrder(moveItem(categories, from, to))
    setDraggedKey(null)
  }

  const toggleCategoryAnalytes = (
    category: ReportCategory,
    visible: boolean,
  ) => {
    const ids = new Set(categoryAnalyteIds(category))
    const hidden = visible
      ? config.hidden_analyte_ids.filter((id) => !ids.has(id))
      : [...new Set([...config.hidden_analyte_ids, ...ids])]
    update({ ...config, hidden_analyte_ids: hidden })
  }

  const toggleAnalyte = (analyteId: string, visible: boolean) => {
    const hidden = visible
      ? config.hidden_analyte_ids.filter((id) => id !== analyteId)
      : [...new Set([...config.hidden_analyte_ids, analyteId])]
    update({ ...config, hidden_analyte_ids: hidden })
  }

  const togglePageBreak = (categoryKey: string, enabled: boolean) => {
    update({
      ...config,
      category_page_breaks: {
        ...config.category_page_breaks,
        [categoryKey]: enabled,
      },
    })
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[calc(100vw-1rem)] overflow-hidden p-0 sm:max-w-xl">
        <SheetHeader className="border-b pr-12">
          <SheetTitle>Configurer le rendu</SheetTitle>
          <SheetDescription>
            {readOnly
              ? "Configuration figée pour cette version publiée."
              : "Ces réglages seront enregistrés avec la version publiée."}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-5 p-4">
            <section className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-medium">Ordre des catégories</h3>
                  <p className="text-xs text-muted-foreground">
                    Glissez les lignes ou utilisez les flèches.
                  </p>
                </div>
              </div>
              <ul className="divide-y rounded-md border bg-background">
                {categories.map((category, index) => {
                  const key = reportCategoryKey(category)
                  return (
                    <li
                      key={key}
                      draggable={!readOnly}
                      onDragStart={() => setDraggedKey(key)}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={() => handleDrop(key)}
                      onDragEnd={() => setDraggedKey(null)}
                      className={cn(
                        "grid grid-cols-[auto_1fr_auto] items-center gap-2 px-3 py-2",
                        draggedKey === key && "bg-accent/50",
                        readOnly && "bg-muted/30",
                      )}
                    >
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <GripVertical className="size-4 cursor-grab" />
                        <span className="w-6 text-right tabular-nums">
                          {index + 1}
                        </span>
                      </div>
                      <span className="min-w-0 truncate font-medium">
                        {category.name}
                      </span>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          disabled={readOnly || index === 0}
                          onClick={() => moveCategory(index, index - 1)}
                          aria-label={`Monter ${category.name}`}
                        >
                          <ArrowUp className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          disabled={readOnly || index === categories.length - 1}
                          onClick={() => moveCategory(index, index + 1)}
                          aria-label={`Descendre ${category.name}`}
                        >
                          <ArrowDown className="size-4" />
                        </Button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </section>

            <section className="space-y-3">
              <h3 className="text-sm font-medium">Visibilité et impression</h3>
              {categories.map((category) => {
                const key = reportCategoryKey(category)
                const ids = categoryAnalyteIds(category)
                const visibleCount = ids.filter(
                  (id) => !config.hidden_analyte_ids.includes(id),
                ).length
                const allVisible = visibleCount === ids.length
                const allVisibleId = `report-render-all-${key}`
                const pageBreakId = `report-render-break-${key}`

                return (
                  <div key={key} className="rounded-md border bg-background">
                    <div className="space-y-3 border-b p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {category.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {visibleCount}/{ids.length} lignes visibles
                          </p>
                        </div>
                        {allVisible ? (
                          <Eye className="size-4 text-primary" />
                        ) : (
                          <EyeOff className="size-4 text-muted-foreground" />
                        )}
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <label
                          htmlFor={allVisibleId}
                          className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                        >
                          <span>Afficher tous les résultats</span>
                          <Switch
                            id={allVisibleId}
                            size="sm"
                            checked={allVisible}
                            disabled={readOnly}
                            onCheckedChange={(checked) =>
                              toggleCategoryAnalytes(category, checked)
                            }
                          />
                        </label>
                        <label
                          htmlFor={pageBreakId}
                          className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                        >
                          <span className="inline-flex items-center gap-2">
                            <FileSymlink className="size-4" />
                            Nouvelle page
                          </span>
                          <Switch
                            id={pageBreakId}
                            size="sm"
                            checked={config.category_page_breaks[key] === true}
                            disabled={readOnly}
                            onCheckedChange={(checked) =>
                              togglePageBreak(key, checked)
                            }
                          />
                        </label>
                      </div>
                    </div>

                    <div className="divide-y">
                      {category.tests.map((test) => (
                        <details
                          key={test.order_item_id}
                          className="group"
                          open
                        >
                          <summary className="cursor-pointer list-none px-3 py-2 text-sm font-medium outline-none transition-colors hover:bg-muted/60 focus-visible:bg-muted">
                            {test.catalog_name}
                          </summary>
                          <div className="space-y-2 px-3 pb-3">
                            {test.analytes.map((analyte) => {
                              const visible =
                                !config.hidden_analyte_ids.includes(
                                  analyte.analyte_id,
                                )
                              const analyteControlId = `report-render-${test.order_item_id}-${analyte.analyte_id}`
                              return (
                                <div
                                  key={analyte.analyte_id}
                                  className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-md border px-3 py-2"
                                >
                                  <Checkbox
                                    id={analyteControlId}
                                    checked={visible}
                                    disabled={readOnly}
                                    onCheckedChange={(checked) =>
                                      toggleAnalyte(
                                        analyte.analyte_id,
                                        checked === true,
                                      )
                                    }
                                  />
                                  <label
                                    htmlFor={analyteControlId}
                                    className="min-w-0 truncate"
                                  >
                                    {analyte.analyte_name}
                                  </label>
                                  <span className="text-muted-foreground">
                                    {analyte.result_value || "—"}
                                  </span>
                                </div>
                              )
                            })}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                )
              })}
            </section>
          </div>
        </ScrollArea>

        <SheetFooter className="border-t">
          <Button
            type="button"
            variant="outline"
            disabled={readOnly}
            onClick={() => update(defaultReportRenderConfig())}
          >
            <RotateCcw className="size-4" />
            Réinitialiser le rendu
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
