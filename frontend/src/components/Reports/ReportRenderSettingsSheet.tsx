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
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Slider } from "@/components/ui/slider"
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

const INTERPRETATION_SECTION_KEY = "interpretation"

type ReportSection =
  | {
      kind: "category"
      key: string
      name: string
      category: ReportCategory
    }
  | {
      kind: "interpretation"
      key: typeof INTERPRETATION_SECTION_KEY
      name: string
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

function hasInterpretation(snapshot: ReportSnapshot) {
  return Boolean(snapshot.interpretation?.html)
}

function orderedSections(
  snapshot: ReportSnapshot,
  config: ReportRenderConfig,
): ReportSection[] {
  const categories = orderedCategories(snapshot, config)
  const sectionsByKey = new Map<string, ReportSection>(
    categories.map((category) => {
      const key = reportCategoryKey(category)
      return [
        key,
        {
          kind: "category",
          key,
          name: category.name,
          category,
        },
      ]
    }),
  )
  if (hasInterpretation(snapshot)) {
    sectionsByKey.set(INTERPRETATION_SECTION_KEY, {
      kind: "interpretation",
      key: INTERPRETATION_SECTION_KEY,
      name: "Interprétation",
    })
  }
  const orderedKeys = [
    ...config.section_order.filter(
      (key) => key !== "footer" && sectionsByKey.has(key),
    ),
    ...categories
      .map(reportCategoryKey)
      .filter((key) => !config.section_order.includes(key)),
    ...(hasInterpretation(snapshot) &&
    !config.section_order.includes(INTERPRETATION_SECTION_KEY)
      ? [INTERPRETATION_SECTION_KEY]
      : []),
  ]

  return orderedKeys
    .map((key) => sectionsByKey.get(key))
    .filter((section): section is ReportSection => Boolean(section))
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
  const sections = useMemo(
    () => orderedSections(snapshot, config),
    [snapshot, config],
  )
  const [draggedKey, setDraggedKey] = useState<string | null>(null)

  useEffect(() => {
    setDraggedKey(null)
  }, [])

  const update = (next: ReportRenderConfig) => {
    if (!readOnly) onChange(next)
  }

  const setSectionOrder = (sectionsInOrder: ReportSection[]) => {
    update({
      ...config,
      section_order: sectionsInOrder
        .map((section) => section.key)
        .filter((key) => key !== "footer"),
      category_order: sectionsInOrder
        .filter(
          (section): section is Extract<ReportSection, { kind: "category" }> =>
            section.kind === "category",
        )
        .map((section) => section.key),
    })
  }

  const moveSection = (from: number, to: number) => {
    setSectionOrder(moveItem(sections, from, to))
  }

  const handleSectionDrop = (targetKey: string) => {
    if (!draggedKey || draggedKey === targetKey || readOnly) return
    const from = sections.findIndex((section) => section.key === draggedKey)
    const to = sections.findIndex((section) => section.key === targetKey)
    if (from === -1 || to === -1) return
    setSectionOrder(moveItem(sections, from, to))
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

  const toggleInterpretationPageBreak = (enabled: boolean) => {
    update({
      ...config,
      interpretation_page_break: enabled,
    })
  }

  const setFooterSpacing = (value: number) => {
    update({
      ...config,
      footer_spacing_mm: Math.min(40, Math.max(0, value)),
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
                  <h3 className="text-sm font-medium">Ordre du rapport</h3>
                  <p className="text-xs text-muted-foreground">
                    Déplacez les catégories et l'interprétation.
                  </p>
                </div>
              </div>
              <ul className="divide-y rounded-md border bg-background">
                {sections.map((section, index) => {
                  const key = section.key
                  return (
                    <li
                      key={key}
                      draggable={!readOnly}
                      onDragStart={() => setDraggedKey(key)}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={() => handleSectionDrop(key)}
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
                        {section.name}
                        {section.kind === "interpretation" && (
                          <span className="ml-2 text-xs font-normal text-muted-foreground">
                            Section
                          </span>
                        )}
                      </span>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          disabled={readOnly || index === 0}
                          onClick={() => moveSection(index, index - 1)}
                          aria-label={`Monter ${section.name}`}
                        >
                          <ArrowUp className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          disabled={readOnly || index === sections.length - 1}
                          onClick={() => moveSection(index, index + 1)}
                          aria-label={`Descendre ${section.name}`}
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
              <div className="rounded-md border bg-background p-3">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">
                      Espace avant le pied de page
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Ajuste le vide entre la fin du rapport et le pied de page.
                    </p>
                  </div>
                  <div className="flex w-24 items-center gap-2">
                    <Input
                      type="number"
                      min={0}
                      max={40}
                      step={1}
                      value={config.footer_spacing_mm}
                      disabled={readOnly}
                      onChange={(event) =>
                        setFooterSpacing(Number(event.currentTarget.value) || 0)
                      }
                      className="text-right"
                    />
                    <span className="text-xs text-muted-foreground">mm</span>
                  </div>
                </div>
                <Slider
                  min={0}
                  max={40}
                  step={1}
                  value={[config.footer_spacing_mm]}
                  disabled={readOnly}
                  onValueChange={([value]) => setFooterSpacing(value ?? 0)}
                />
              </div>
              {hasInterpretation(snapshot) && (
                <div className="rounded-md border bg-background p-3">
                  <label
                    htmlFor="report-render-break-interpretation"
                    className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                  >
                    <span className="inline-flex items-center gap-2">
                      <FileSymlink className="size-4" />
                      Nouvelle page avant l'interprétation
                    </span>
                    <Switch
                      id="report-render-break-interpretation"
                      size="sm"
                      checked={config.interpretation_page_break}
                      disabled={readOnly}
                      onCheckedChange={toggleInterpretationPageBreak}
                    />
                  </label>
                </div>
              )}
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
