import { useSuspenseQuery } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import { UnitsService } from "@/client"
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

import { columns } from "./columns"
import { UniteDialog } from "./UniteDialog"

type StatusFilter = "active" | "deleted" | "all"

function getUnitsQueryOptions(statusFilter: StatusFilter) {
  return {
    queryKey: ["units", { includeDeleted: statusFilter }],
    queryFn: () =>
      UnitsService.readUnits({
        limit: 200,
        includeDeleted: statusFilter !== "active" || undefined,
      }),
  }
}

function UnitesSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

export function UnitesView() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [showFilters, setShowFilters] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  const activeFilterCount = statusFilter !== "active" ? 1 : 0
  const hasActive = activeFilterCount > 0 || search.trim() !== ""

  const resetAll = () => {
    setSearch("")
    setStatusFilter("active")
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher une unité…"
            className="pl-9"
            aria-label="Rechercher dans la table"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            onClick={() => setShowFilters((s) => !s)}
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
          <Button onClick={() => setDialogOpen(true)}>
            <Plus />
            Ajouter une unité
          </Button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-status-units"
                className="text-xs font-medium text-muted-foreground"
              >
                Statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as StatusFilter)}
              >
                <SelectTrigger
                  id="filter-status-units"
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
              disabled={!hasActive}
              className="text-muted-foreground"
            >
              <X className="size-4" />
              Réinitialiser
            </Button>
          </div>
        </div>
      )}

      {/* Table */}
      <Suspense fallback={<UnitesSkeleton />}>
        <UnitesTableWithMeta
          search={search}
          statusFilter={statusFilter}
          hasActive={hasActive}
        />
      </Suspense>

      {/* Create dialog */}
      <UniteDialog open={dialogOpen} onOpenChange={setDialogOpen} unit={null} />
    </div>
  )
}

function UnitesTableWithMeta({
  search,
  statusFilter,
  hasActive,
}: {
  search: string
  statusFilter: StatusFilter
  hasActive: boolean
}) {
  const { data: unitsData } = useSuspenseQuery(
    getUnitsQueryOptions(statusFilter),
  )

  const filtered = useMemo(() => {
    let rows = unitsData.data

    if (statusFilter === "active") {
      rows = rows.filter((u) => !u.is_deleted)
    } else if (statusFilter === "deleted") {
      rows = rows.filter((u) => u.is_deleted)
    }

    const q = search.toLowerCase().trim()
    if (q) {
      rows = rows.filter((u) => u.name.toLowerCase().includes(q))
    }

    return rows
  }, [unitsData, search, statusFilter])

  if (filtered.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <Search />
        </EmptyMedia>
        <EmptyTitle>Aucune unité trouvée</EmptyTitle>
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
          unité{filtered.length !== 1 && "s"}
          {hasActive && (
            <span>
              {" "}
              · filtrée{filtered.length !== 1 && "s"} de {unitsData.data.length}
            </span>
          )}
        </span>
      </div>
      <SimpleTable columns={columns} data={filtered} />
    </>
  )
}
