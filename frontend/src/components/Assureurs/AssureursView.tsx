import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { useMemo, useState } from "react"

import type { SortOrder } from "@/client"
import { InsuranceProvidersService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { AssureurDialog } from "./AssureurDialog"
import { assureurExportColumns, getAssureurColumns } from "./columns"

type StatusFilter = "active" | "deleted" | "all"
type AssureurSortBy = "name" | "created_at"

export function AssureursView() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [sortBy, setSortBy] = useState<AssureurSortBy>("name")
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc")
  const [showFilters, setShowFilters] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  const activeFilterCount = statusFilter !== "active" ? 1 : 0
  const hasActiveFilters = activeFilterCount > 0 || search.trim() !== ""

  const providersQuery = useQuery({
    queryKey: [
      "insurance-providers",
      { page, pageSize, search, statusFilter, sortBy, sortOrder },
    ],
    queryFn: () =>
      InsuranceProvidersService.readInsuranceProviders({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: statusFilter !== "active" || undefined,
        isDeleted:
          statusFilter === "all" ? undefined : statusFilter === "deleted",
        sortBy,
        sortOrder,
      }),
  })

  const columns = useMemo(
    () =>
      getAssureurColumns(() => {
        queryClient.invalidateQueries({ queryKey: ["insurance-providers"] })
      }),
    [queryClient],
  )

  const onSort = (nextSortBy: AssureurSortBy) => {
    if (sortBy === nextSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(nextSortBy)
      setSortOrder("asc")
    }
    setPage(0)
  }

  const resetFilters = () => {
    setSearch("")
    setStatusFilter("active")
    setPage(0)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            placeholder="Rechercher un assureur…"
            className="pl-9"
            aria-label="Rechercher"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            onClick={() => setShowFilters((value) => !value)}
          >
            <SlidersHorizontal className="size-4" />
            Filtres
            {activeFilterCount > 0 && (
              <Badge className="ml-1 bg-primary text-primary-foreground">
                {activeFilterCount}
              </Badge>
            )}
          </Button>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus />
            Ajouter
          </Button>
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-status-ip"
                className="text-xs font-medium text-muted-foreground"
              >
                Statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(value) => {
                  setStatusFilter(value as StatusFilter)
                  setPage(0)
                }}
              >
                <SelectTrigger id="filter-status-ip" size="sm" className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Actifs</SelectItem>
                  <SelectItem value="deleted">Supprimés</SelectItem>
                  <SelectItem value="all">Tous</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetFilters}
              disabled={!hasActiveFilters}
              className="text-muted-foreground"
            >
              <X className="size-4" />
              Réinitialiser
            </Button>
          </div>
        </div>
      )}

      <ServerDataTable
        columns={columns}
        data={providersQuery.data?.data ?? []}
        loading={providersQuery.isLoading}
        totalCount={providersQuery.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          name: "name",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as AssureurSortBy)}
        emptyMessage="Aucun assureur trouvé."
        exportFilename="assureurs.csv"
        exportColumns={assureurExportColumns()}
      />

      <AssureurDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        item={null}
      />
    </div>
  )
}
