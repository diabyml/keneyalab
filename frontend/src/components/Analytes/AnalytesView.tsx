import { useQuery } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { useMemo, useState } from "react"

import type { AnalyteDataType } from "@/client"
import { AnalytesService, UnitsService } from "@/client"
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
import { AnalyteDialog } from "./AnalyteDialog"
import { getColumns } from "./columns"
import { DATA_TYPE_LABELS, DATA_TYPE_OPTIONS } from "./labels"

type StatusFilter = "active" | "deleted" | "all"
type CalculatedFilter = "all" | "calculated" | "not_calculated"
type DataTypeFilter = "all" | AnalyteDataType

function getAnalytesQueryOptions({
  search,
  statusFilter,
  dataTypeFilter,
  calculatedFilter,
  page,
  pageSize,
}: {
  search: string
  statusFilter: StatusFilter
  dataTypeFilter: DataTypeFilter
  calculatedFilter: CalculatedFilter
  page: number
  pageSize: number
}) {
  return {
    queryKey: [
      "analytes",
      {
        search,
        statusFilter,
        dataTypeFilter,
        calculatedFilter,
        page,
        pageSize,
      },
    ],
    queryFn: () =>
      AnalytesService.readAnalytes({
        skip: page * pageSize,
        limit: pageSize,
        includeDeleted: statusFilter !== "active",
        isDeleted: statusFilter === "deleted" ? true : undefined,
        dataType: dataTypeFilter === "all" ? undefined : dataTypeFilter,
        isCalculated:
          calculatedFilter === "all"
            ? undefined
            : calculatedFilter === "calculated",
        search: search.trim() || undefined,
      }),
  }
}

export function AnalytesView() {
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [dataTypeFilter, setDataTypeFilter] = useState<DataTypeFilter>("all")
  const [calculatedFilter, setCalculatedFilter] =
    useState<CalculatedFilter>("all")
  const [showFilters, setShowFilters] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  const activeFilterCount =
    (statusFilter !== "active" ? 1 : 0) +
    (dataTypeFilter !== "all" ? 1 : 0) +
    (calculatedFilter !== "all" ? 1 : 0)
  const hasActive = activeFilterCount > 0 || search.trim() !== ""

  const resetAll = () => {
    setSearch("")
    setStatusFilter("active")
    setDataTypeFilter("all")
    setCalculatedFilter("all")
    setPage(0)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(0)
            }}
            placeholder="Rechercher un analyte…"
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
            Ajouter un analyte
          </Button>
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-status-analytes"
                className="text-xs font-medium text-muted-foreground"
              >
                Statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(v) => {
                  setStatusFilter(v as StatusFilter)
                  setPage(0)
                }}
              >
                <SelectTrigger
                  id="filter-status-analytes"
                  size="sm"
                  className="w-44"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Actifs</SelectItem>
                  <SelectItem value="deleted">Supprimés</SelectItem>
                  <SelectItem value="all">Tous</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-type-analytes"
                className="text-xs font-medium text-muted-foreground"
              >
                Type
              </label>
              <Select
                value={dataTypeFilter}
                onValueChange={(v) => {
                  setDataTypeFilter(v as DataTypeFilter)
                  setPage(0)
                }}
              >
                <SelectTrigger
                  id="filter-type-analytes"
                  size="sm"
                  className="w-44"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  {DATA_TYPE_OPTIONS.map((type) => (
                    <SelectItem key={type} value={type}>
                      {DATA_TYPE_LABELS[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-calculated-analytes"
                className="text-xs font-medium text-muted-foreground"
              >
                Calculé
              </label>
              <Select
                value={calculatedFilter}
                onValueChange={(v) => {
                  setCalculatedFilter(v as CalculatedFilter)
                  setPage(0)
                }}
              >
                <SelectTrigger
                  id="filter-calculated-analytes"
                  size="sm"
                  className="w-44"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="calculated">Calculés</SelectItem>
                  <SelectItem value="not_calculated">Non calculés</SelectItem>
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

      <AnalytesTableWithMeta
        search={search}
        statusFilter={statusFilter}
        dataTypeFilter={dataTypeFilter}
        calculatedFilter={calculatedFilter}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
      />

      <AnalyteDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        analyte={null}
      />
    </div>
  )
}

function AnalytesTableWithMeta({
  search,
  statusFilter,
  dataTypeFilter,
  calculatedFilter,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: {
  search: string
  statusFilter: StatusFilter
  dataTypeFilter: DataTypeFilter
  calculatedFilter: CalculatedFilter
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}) {
  const analytesQuery = useQuery(
    getAnalytesQueryOptions({
      search,
      statusFilter,
      dataTypeFilter,
      calculatedFilter,
      page,
      pageSize,
    }),
  )
  const unitsQuery = useQuery({
    queryKey: ["units", { includeDeleted: "active" }],
    queryFn: () => UnitsService.readUnits({ limit: 500 }),
  })

  const unitsById = useMemo(
    () =>
      new Map(
        (unitsQuery.data?.data ?? []).map((unit) => [unit.id, unit.name]),
      ),
    [unitsQuery.data],
  )

  return (
    <ServerDataTable
      columns={getColumns(unitsById)}
      data={analytesQuery.data?.data ?? []}
      loading={analytesQuery.isLoading || unitsQuery.isLoading}
      totalCount={analytesQuery.data?.count ?? 0}
      page={page}
      pageSize={pageSize}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      emptyMessage="Aucun analyte trouvé."
      exportFilename="analytes.csv"
      exportColumns={[
        { header: "Code", value: (row) => row.code },
        { header: "Nom", value: (row) => row.name },
        { header: "Type", value: (row) => DATA_TYPE_LABELS[row.data_type] },
        {
          header: "Unité",
          value: (row) =>
            row.unit_id ? (unitsById.get(row.unit_id) ?? "") : "",
        },
        {
          header: "Calculé",
          value: (row) => (row.is_calculated ? "Oui" : "Non"),
        },
        {
          header: "Statut",
          value: (row) => (row.is_deleted ? "Supprimé" : "Actif"),
        },
      ]}
    />
  )
}
