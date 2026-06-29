import { useQuery } from "@tanstack/react-query"
import { ChevronDown, ChevronRight, FlaskConical, Search } from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import type { CatalogDetailPublic, CatalogSummaryPublic } from "@/client"
import { CategoriesService, OrdersService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { formatMoney } from "./utils"

interface CatalogPickerProps {
  selected: Map<string, CatalogDetailPublic>
  onChange: (selected: Map<string, CatalogDetailPublic>) => void
}

export function CatalogPicker({ selected, onChange }: CatalogPickerProps) {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [type, setType] = useState<"all" | "item" | "panel">("all")
  const [categoryId, setCategoryId] = useState<string | null>(null)
  const [categoryOption, setCategoryOption] =
    useState<SearchSelectOption | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedSearch(search), 250)
    return () => window.clearTimeout(timeout)
  }, [search])

  const query = useQuery({
    queryKey: ["order-catalog-options", debouncedSearch, type, categoryId],
    queryFn: () =>
      OrdersService.readOrderCatalogOptions({
        search: debouncedSearch.trim() || undefined,
        type: type === "all" ? undefined : type,
        categoryId: categoryId || undefined,
        limit: 10_000,
      }),
  })

  const loadCategories = useCallback(
    async (value: string): Promise<SearchSelectOption[]> => {
      const response = await CategoriesService.readCategories({
        search: value || undefined,
        limit: 20,
      })
      return response.data.map((category) => ({
        value: category.id,
        label: category.name,
      }))
    },
    [],
  )

  const addEntries = async (entries: CatalogSummaryPublic[]) => {
    const next = new Map(selected)
    const missing = entries.filter((entry) => !next.has(entry.id))
    const details = await Promise.all(
      missing.map((entry) =>
        OrdersService.readOrderCatalogOption({ id: entry.id }),
      ),
    )
    for (const detail of details) next.set(detail.id, detail)
    onChange(next)
    setSearch("")
    setDebouncedSearch("")
  }

  const toggleEntry = async (entry: CatalogSummaryPublic) => {
    if (selected.has(entry.id)) {
      const next = new Map(selected)
      next.delete(entry.id)
      onChange(next)
      return
    }
    await addEntries([entry])
    if (entry.type === "panel") {
      setExpanded((current) => new Set(current).add(entry.id))
    }
  }

  const visible = query.data?.data ?? []

  return (
    <section className="space-y-3">
      <div className="flex flex-col gap-2 xl:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && visible.length > 0) {
                event.preventDefault()
                void addEntries(visible)
              }
            }}
            className="pl-9"
            placeholder="Rechercher code ou nom, Entrée pour tout ajouter…"
          />
        </div>
        <Select
          value={type}
          onValueChange={(value) => setType(value as typeof type)}
        >
          <SelectTrigger className="w-full xl:w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tests et panels</SelectItem>
            <SelectItem value="item">Tests</SelectItem>
            <SelectItem value="panel">Panels</SelectItem>
          </SelectContent>
        </Select>
        <div className="w-full xl:w-64">
          <SearchSelect
            value={categoryId}
            selectedOption={categoryOption}
            onValueChange={(value, option) => {
              setCategoryId(value)
              setCategoryOption(option ?? null)
            }}
            loadOptions={loadCategories}
            placeholder="Toutes les catégories"
            searchPlaceholder="Rechercher une catégorie…"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-md border">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] border-b bg-muted/30 px-3 py-2 text-xs font-medium text-muted-foreground">
          <span>Catalogue</span>
          <span>Prix</span>
        </div>
        <div className="max-h-[420px] overflow-y-auto">
          {query.isLoading ? (
            <div className="p-6 text-center text-sm text-muted-foreground">
              Recherche…
            </div>
          ) : visible.length === 0 ? (
            <div className="p-6 text-center text-sm text-muted-foreground">
              Aucun test ou panel trouvé.
            </div>
          ) : (
            visible.map((entry) => {
              const detail = selected.get(entry.id)
              const isExpanded = expanded.has(entry.id)
              return (
                <div key={entry.id} className="border-b last:border-b-0">
                  <div
                    className={cn(
                      "grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-3 py-3 text-left hover:bg-muted/40",
                      selected.has(entry.id) && "bg-primary/5",
                    )}
                  >
                    <Checkbox
                      checked={selected.has(entry.id)}
                      onCheckedChange={() => void toggleEntry(entry)}
                      aria-label={`${selected.has(entry.id) ? "Retirer" : "Ajouter"} ${entry.name}`}
                    />
                    <button
                      type="button"
                      onClick={() => void toggleEntry(entry)}
                      className="col-span-2 grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 text-left"
                    >
                      <span className="min-w-0">
                        <span className="flex items-center gap-2">
                          <span className="truncate font-medium">
                            {entry.name}
                          </span>
                          <Badge variant="outline" className="shrink-0">
                            {entry.type === "panel" ? "Panel" : "Test"}
                          </Badge>
                        </span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {entry.code}
                          {entry.category_name
                            ? ` · ${entry.category_name}`
                            : ""}
                        </span>
                      </span>
                      <span className="tabular-nums">
                        {formatMoney(entry.price ?? 0)}
                      </span>
                    </button>
                  </div>
                  {entry.type === "panel" && detail && (
                    <div className="border-t bg-muted/15">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="ml-9"
                        onClick={() =>
                          setExpanded((current) => {
                            const next = new Set(current)
                            if (next.has(entry.id)) next.delete(entry.id)
                            else next.add(entry.id)
                            return next
                          })
                        }
                      >
                        {isExpanded ? (
                          <ChevronDown className="size-4" />
                        ) : (
                          <ChevronRight className="size-4" />
                        )}
                        {(detail.panel_items ?? []).length} test
                        {(detail.panel_items ?? []).length !== 1 && "s"} ajouté
                        {(detail.panel_items ?? []).length !== 1 && "s"}
                      </Button>
                      {isExpanded && (
                        <div className="pb-2 pl-14 pr-3">
                          {(detail.panel_items ?? []).map((item) => (
                            <div
                              key={item.id}
                              className="flex items-center justify-between gap-3 py-1.5 text-sm"
                            >
                              <span className="flex min-w-0 items-center gap-2">
                                <FlaskConical className="size-3.5 shrink-0 text-muted-foreground" />
                                <span className="truncate">
                                  {item.test_code} · {item.test_name}
                                </span>
                              </span>
                              <span className="shrink-0 tabular-nums text-muted-foreground">
                                {formatMoney(item.test_price ?? 0)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        {selected.size} sélection{selected.size !== 1 && "s"} · Entrée ajoute
        les {visible.length} résultats visibles.
      </p>
    </section>
  )
}
