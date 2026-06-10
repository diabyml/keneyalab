import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import {
  ArrowDown,
  ArrowUp,
  GripVertical,
  Plus,
  RotateCcw,
  Save,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react"
import { Suspense, useEffect, useMemo, useState } from "react"

import type { CategoryPublic } from "@/client"
import { CategoriesService } from "@/client"
import { SimpleTable } from "@/components/Common/SimpleTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyDescription,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"
import { CategoryDialog } from "./CategoryDialog"
import { columns } from "./columns"

type StatusFilter = "active" | "deleted" | "all"

function getCategoriesQueryOptions(statusFilter: StatusFilter) {
  return {
    queryKey: ["categories", { includeDeleted: statusFilter }],
    queryFn: () =>
      CategoriesService.readCategories({
        limit: 500,
        includeDeleted: statusFilter !== "active" || undefined,
      }),
  }
}

function CategoriesSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

function sortCategories(rows: CategoryPublic[]) {
  return [...rows].sort((a, b) => {
    const aOrder = a.sort_order ?? 0
    const bOrder = b.sort_order ?? 0
    if (aOrder !== bOrder) return aOrder - bOrder
    return a.name.localeCompare(b.name, "fr")
  })
}

export function CategoriesView() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [showFilters, setShowFilters] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [reorderMode, setReorderMode] = useState(false)

  const activeFilterCount = statusFilter !== "active" ? 1 : 0
  const hasActive = activeFilterCount > 0 || search.trim() !== ""
  const canReorder = statusFilter === "active" && search.trim() === ""

  const resetAll = () => {
    setSearch("")
    setStatusFilter("active")
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher une catégorie…"
            className="pl-9"
            aria-label="Rechercher dans la table"
            disabled={reorderMode}
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            onClick={() => setShowFilters((s) => !s)}
            disabled={reorderMode}
          >
            <SlidersHorizontal className="size-4" />
            Filtres
            {activeFilterCount > 0 && (
              <Badge
                variant="secondary"
                className="ml-1 bg-primary text-primary-foreground"
              >
                {activeFilterCount}
              </Badge>
            )}
          </Button>
          <Button
            variant={reorderMode ? "secondary" : "outline"}
            size="sm"
            onClick={() => setReorderMode((v) => !v)}
            disabled={!canReorder}
          >
            <GripVertical className="size-4" />
            Réorganiser
          </Button>
          <Button onClick={() => setDialogOpen(true)} disabled={reorderMode}>
            <Plus />
            Ajouter une catégorie
          </Button>
        </div>
      </div>

      {!canReorder && !reorderMode && (
        <p className="text-sm text-muted-foreground">
          Réinitialisez la recherche et affichez les catégories actives pour
          modifier l'ordre.
        </p>
      )}

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-status-categories"
                className="text-xs font-medium text-muted-foreground"
              >
                Statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as StatusFilter)}
                disabled={reorderMode}
              >
                <SelectTrigger
                  id="filter-status-categories"
                  size="sm"
                  className="w-44"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Actives</SelectItem>
                  <SelectItem value="deleted">Supprimées</SelectItem>
                  <SelectItem value="all">Toutes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetAll}
              disabled={!hasActive || reorderMode}
              className="text-muted-foreground"
            >
              <X className="size-4" />
              Réinitialiser
            </Button>
          </div>
        </div>
      )}

      <Suspense fallback={<CategoriesSkeleton />}>
        <CategoriesTableWithMeta
          search={search}
          statusFilter={statusFilter}
          hasActive={hasActive}
          reorderMode={reorderMode}
          onReorderModeChange={setReorderMode}
        />
      </Suspense>

      <Suspense fallback={null}>
        <CreateCategoryDialog open={dialogOpen} onOpenChange={setDialogOpen} />
      </Suspense>
    </div>
  )
}

function CreateCategoryDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { data } = useSuspenseQuery(getCategoriesQueryOptions("all"))
  const nextSortOrder =
    data.data.reduce((max, item) => Math.max(max, item.sort_order ?? 0), 0) + 1

  return (
    <CategoryDialog
      open={open}
      onOpenChange={onOpenChange}
      category={null}
      nextSortOrder={nextSortOrder}
    />
  )
}

function CategoriesTableWithMeta({
  search,
  statusFilter,
  hasActive,
  reorderMode,
  onReorderModeChange,
}: {
  search: string
  statusFilter: StatusFilter
  hasActive: boolean
  reorderMode: boolean
  onReorderModeChange: (value: boolean) => void
}) {
  const { data } = useSuspenseQuery(getCategoriesQueryOptions(statusFilter))

  const filtered = useMemo(() => {
    let rows = data.data

    if (statusFilter === "active") {
      rows = rows.filter((category) => !category.is_deleted)
    } else if (statusFilter === "deleted") {
      rows = rows.filter((category) => category.is_deleted)
    }

    const q = search.toLowerCase().trim()
    if (q) {
      rows = rows.filter((category) => category.name.toLowerCase().includes(q))
    }

    return sortCategories(rows)
  }, [data, search, statusFilter])

  const activeRows = useMemo(
    () => sortCategories(data.data.filter((category) => !category.is_deleted)),
    [data],
  )

  if (filtered.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <Search />
        </EmptyMedia>
        <EmptyTitle>Aucune catégorie trouvée</EmptyTitle>
        <EmptyDescription>
          Essayez d'ajuster votre recherche ou vos filtres.
        </EmptyDescription>
      </Empty>
    )
  }

  return (
    <>
      <div className="flex items-center px-0.5 text-sm text-muted-foreground">
        <span>
          <span className="font-medium text-foreground">{filtered.length}</span>{" "}
          catégorie{filtered.length !== 1 && "s"}
          {hasActive && (
            <span>
              {" "}
              · filtrée{filtered.length !== 1 && "s"} de {data.data.length}
            </span>
          )}
        </span>
      </div>
      {reorderMode ? (
        <CategoriesReorderPanel
          categories={activeRows}
          onCancel={() => onReorderModeChange(false)}
          onSaved={() => onReorderModeChange(false)}
        />
      ) : (
        <SimpleTable columns={columns} data={filtered} />
      )}
    </>
  )
}

function moveItem<T>(items: T[], from: number, to: number) {
  const next = [...items]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

function CategoriesReorderPanel({
  categories,
  onCancel,
  onSaved,
}: {
  categories: CategoryPublic[]
  onCancel: () => void
  onSaved: () => void
}) {
  const [items, setItems] = useState(categories)
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  useEffect(() => {
    setItems(categories)
  }, [categories])

  const mutation = useMutation({
    mutationFn: () =>
      CategoriesService.reorderCategories({
        requestBody: {
          items: items.map((item, index) => ({
            id: item.id,
            sort_order: index + 1,
          })),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Ordre des catégories enregistré")
      onSaved()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
    },
  })

  const move = (from: number, to: number) => {
    if (to < 0 || to >= items.length) return
    setItems((current) => moveItem(current, from, to))
  }

  const handleDrop = (targetId: string) => {
    if (!draggedId || draggedId === targetId) return
    const from = items.findIndex((item) => item.id === draggedId)
    const to = items.findIndex((item) => item.id === targetId)
    if (from === -1 || to === -1) return
    setItems((current) => moveItem(current, from, to))
    setDraggedId(null)
  }

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-medium">Réorganiser les catégories</h2>
          <p className="text-sm text-muted-foreground">
            Glissez les lignes ou utilisez les flèches, puis enregistrez
            l'ordre.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onCancel}
            disabled={mutation.isPending}
          >
            <RotateCcw className="size-4" />
            Annuler
          </Button>
          <Button
            size="sm"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || items.length === 0}
          >
            <Save className="size-4" />
            Enregistrer l'ordre
          </Button>
        </div>
      </div>
      <ul className="divide-y">
        {items.map((item, index) => (
          <li
            key={item.id}
            aria-label={`${item.name}, position ${index + 1}`}
            draggable
            onDragStart={() => setDraggedId(item.id)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => handleDrop(item.id)}
            onDragEnd={() => setDraggedId(null)}
            className={cn(
              "grid grid-cols-[auto_1fr_auto] items-center gap-3 px-4 py-3 transition-colors",
              draggedId === item.id && "bg-accent/50",
            )}
          >
            <div className="flex items-center gap-3 text-muted-foreground">
              <GripVertical className="size-4 cursor-grab" />
              <span className="w-8 text-right text-sm tabular-nums">
                {index + 1}
              </span>
            </div>
            <span className="min-w-0 truncate text-sm font-medium">
              {item.name}
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => move(index, index - 1)}
                disabled={index === 0 || mutation.isPending}
                aria-label={`Monter ${item.name}`}
              >
                <ArrowUp className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => move(index, index + 1)}
                disabled={index === items.length - 1 || mutation.isPending}
                aria-label={`Descendre ${item.name}`}
              >
                <ArrowDown className="size-4" />
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
