import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { SortOrder } from "@/client"
import { DoctorsService, TitlesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
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
import { usePermission } from "@/hooks/usePermission"
import { getDoctorColumns } from "./columns"
import { DoctorDialog } from "./DoctorDialog"
import {
  type DoctorSortBy,
  doctorExportColumns,
  type StatusFilter,
} from "./utils"

export function DoctorsView() {
  const queryClient = useQueryClient()
  const canCreate = usePermission("doctors", "create")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [titleId, setTitleId] = useState<string | null>(null)
  const [selectedTitle, setSelectedTitle] = useState<SearchSelectOption | null>(
    null,
  )
  const [sortBy, setSortBy] = useState<DoctorSortBy>("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [showFilters, setShowFilters] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  const activeFilterCount =
    (statusFilter !== "active" ? 1 : 0) + (titleId ? 1 : 0)

  const doctorsQuery = useQuery({
    queryKey: [
      "doctors",
      {
        page,
        pageSize,
        search,
        statusFilter,
        titleId,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      DoctorsService.readDoctors({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        titleId: titleId || undefined,
        includeDeleted: statusFilter !== "active" || undefined,
        isDeleted:
          statusFilter === "all" ? undefined : statusFilter === "deleted",
        sortBy,
        sortOrder,
      }),
  })

  const loadTitleOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await TitlesService.readTitles({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((title) => ({
        value: title.id,
        label: title.name,
      }))
    },
    [],
  )

  const resetFilters = () => {
    setSearch("")
    setStatusFilter("active")
    setTitleId(null)
    setSelectedTitle(null)
    setPage(0)
  }

  const onSort = (nextSortBy: DoctorSortBy) => {
    if (sortBy === nextSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(nextSortBy)
      setSortOrder("asc")
    }
    setPage(0)
  }

  const columns = useMemo(
    () =>
      getDoctorColumns(() => {
        queryClient.invalidateQueries({ queryKey: ["doctors"] })
      }),
    [queryClient],
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            placeholder="Rechercher nom, téléphone, provenance…"
            className="pl-9"
            aria-label="Rechercher des médecins"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
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
          {canCreate && (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" />
              Nouveau médecin
            </Button>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="doctor-status-filter"
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
                <SelectTrigger
                  id="doctor-status-filter"
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
            <div className="min-w-64 flex-1">
              <div className="mb-1.5 text-xs font-medium text-muted-foreground">
                Titre
              </div>
              <SearchSelect
                value={titleId}
                onValueChange={(value, option) => {
                  setTitleId(value)
                  setSelectedTitle(option ?? null)
                  setPage(0)
                }}
                selectedOption={selectedTitle}
                loadOptions={loadTitleOptions}
                placeholder="Tous les titres"
                searchPlaceholder="Rechercher un titre…"
                emptyMessage="Aucun titre trouvé"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetFilters}
              disabled={activeFilterCount === 0 && search.trim() === ""}
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
        data={doctorsQuery.data?.data ?? []}
        loading={doctorsQuery.isLoading}
        totalCount={doctorsQuery.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          last_name: "last_name",
          provenance: "provenance",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as DoctorSortBy)}
        emptyMessage="Aucun médecin trouvé."
        exportFilename="medecins.csv"
        exportColumns={doctorExportColumns()}
      />

      <DoctorDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        doctor={null}
      />
    </div>
  )
}
