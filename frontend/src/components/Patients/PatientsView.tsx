import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { useMemo, useState } from "react"

import type { SortOrder } from "@/client"
import { PatientsService } from "@/client"
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
import { getPatientColumns } from "./columns"
import { PatientDialog } from "./PatientDialog"
import {
  GENDER_LABELS,
  type GenderFilter,
  type PatientSortBy,
  patientExportColumns,
  type StatusFilter,
} from "./utils"

export function PatientsView() {
  const queryClient = useQueryClient()
  const canCreate = usePermission("patients", "create")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [genderFilter, setGenderFilter] = useState<GenderFilter>("all")
  const [sortBy, setSortBy] = useState<PatientSortBy>("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [showFilters, setShowFilters] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  const activeFilterCount =
    (statusFilter !== "active" ? 1 : 0) + (genderFilter !== "all" ? 1 : 0)

  const patientsQuery = useQuery({
    queryKey: [
      "patients",
      {
        page,
        pageSize,
        search,
        statusFilter,
        genderFilter,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      PatientsService.readPatients({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: statusFilter !== "active" || undefined,
        isDeleted:
          statusFilter === "all" ? undefined : statusFilter === "deleted",
        gender: genderFilter === "all" ? undefined : genderFilter,
        sortBy,
        sortOrder,
      }),
  })

  const resetFilters = () => {
    setSearch("")
    setStatusFilter("active")
    setGenderFilter("all")
    setPage(0)
  }

  const onSort = (nextSortBy: PatientSortBy) => {
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
      getPatientColumns(() => {
        queryClient.invalidateQueries({ queryKey: ["patients"] })
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
            placeholder="Rechercher identifiant, nom, téléphone…"
            className="pl-9"
            aria-label="Rechercher des patients"
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
              Nouveau patient
            </Button>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="patient-status-filter"
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
                  id="patient-status-filter"
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
                htmlFor="patient-gender-filter"
                className="text-xs font-medium text-muted-foreground"
              >
                Sexe
              </label>
              <Select
                value={genderFilter}
                onValueChange={(value) => {
                  setGenderFilter(value as GenderFilter)
                  setPage(0)
                }}
              >
                <SelectTrigger
                  id="patient-gender-filter"
                  size="sm"
                  className="w-44"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="male">{GENDER_LABELS.male}</SelectItem>
                  <SelectItem value="female">{GENDER_LABELS.female}</SelectItem>
                </SelectContent>
              </Select>
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
        data={patientsQuery.data?.data ?? []}
        loading={patientsQuery.isLoading}
        totalCount={patientsQuery.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          identifier: "identifier",
          last_name: "last_name",
          date_of_birth: "date_of_birth",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as PatientSortBy)}
        emptyMessage="Aucun patient trouvé."
        exportFilename="patients.csv"
        exportColumns={patientExportColumns()}
      />

      <PatientDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        patient={null}
      />
    </div>
  )
}
