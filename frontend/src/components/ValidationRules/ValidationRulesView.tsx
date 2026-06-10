import { useQuery } from "@tanstack/react-query"
import { FlaskConical, Plus, Search, SlidersHorizontal } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type {
  AnalyteDataType,
  SortOrder,
  TargetGenderType,
  ValidationRuleDetailPublic,
} from "@/client"
import {
  AnalytesService,
  PatientContextsService,
  ValidationRulesService,
} from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { usePermission } from "@/hooks/usePermission"
import {
  getValidationRuleColumns,
  validationRuleExportColumns,
} from "./columns"
import { DATA_TYPE_LABELS } from "./labels"
import {
  type ActiveFilter,
  ALL,
  type SortBy,
  type ValidationRuleFilterState,
} from "./types"
import { activeToBool, initialFilters } from "./utils"
import { ValidationRuleDialog } from "./ValidationRuleDialog"
import { ValidationRuleFilters } from "./ValidationRuleFilters"
import { ValidationSimulatorSheet } from "./ValidationSimulatorSheet"

export function ValidationRulesView() {
  const canManage = usePermission("rules", "manage")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [sortBy, setSortBy] = useState<SortBy>("priority")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] =
    useState<ValidationRuleFilterState>(initialFilters)
  const [dialogRule, setDialogRule] =
    useState<ValidationRuleDetailPublic | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [simulatorOpen, setSimulatorOpen] = useState(false)

  const loadAnalyteOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await AnalytesService.readAnalytes({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((analyte) => ({
        value: analyte.id,
        label: `${analyte.code} - ${analyte.name}`,
        description: DATA_TYPE_LABELS[analyte.data_type],
      }))
    },
    [],
  )

  const loadContextOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await PatientContextsService.readPatientContexts({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((context) => ({
        value: context.id,
        label: context.name,
      }))
    },
    [],
  )

  const rulesQuery = useQuery({
    queryKey: [
      "validation-rules",
      {
        search,
        page,
        pageSize,
        sortBy,
        sortOrder,
        ...filters,
      },
    ],
    queryFn: () =>
      ValidationRulesService.readValidationRules({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        sortBy,
        sortOrder,
        isActive: activeToBool(filters.activeFilter),
        dataType:
          filters.dataTypeFilter === ALL
            ? undefined
            : (filters.dataTypeFilter as AnalyteDataType),
        targetGender:
          filters.genderFilter === ALL
            ? undefined
            : (filters.genderFilter as TargetGenderType),
        ageYears: filters.ageFilter.trim()
          ? Number(filters.ageFilter)
          : undefined,
        analyteId:
          filters.analyteFilter === ALL ? undefined : filters.analyteFilter,
        requiredContextId:
          filters.contextFilter === ALL ? undefined : filters.contextFilter,
      }),
  })

  const rows = rulesQuery.data?.data ?? []
  const totalCount = rulesQuery.data?.count ?? 0
  const activeFilterCount =
    (filters.activeFilter !== "active" ? 1 : 0) +
    (filters.dataTypeFilter !== ALL ? 1 : 0) +
    (filters.genderFilter !== ALL ? 1 : 0) +
    (filters.ageFilter.trim() ? 1 : 0) +
    (filters.analyteFilter !== ALL ? 1 : 0) +
    (filters.contextFilter !== ALL ? 1 : 0)

  const openDialog = useCallback((rule: ValidationRuleDetailPublic | null) => {
    setDialogRule(rule)
    setDialogOpen(true)
  }, [])

  const columns = useMemo(
    () => getValidationRuleColumns(openDialog),
    [openDialog],
  )

  const updateFilters = (next: Partial<ValidationRuleFilterState>) => {
    setFilters((current) => ({ ...current, ...next }))
    setPage(0)
  }

  const resetFilters = () => {
    setSearch("")
    setFilters(initialFilters())
    setPage(0)
  }

  const onSort = (nextSortBy: SortBy) => {
    if (sortBy === nextSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(nextSortBy)
      setSortOrder(nextSortBy === "priority" ? "desc" : "asc")
    }
    setPage(0)
  }

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
            placeholder="Rechercher un analyte…"
            className="pl-9"
            aria-label="Rechercher dans les règles"
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
          {canManage && (
            <>
              <Button onClick={() => openDialog(null)}>
                <Plus className="size-4" />
                Ajouter une règle
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSimulatorOpen(true)}
              >
                <FlaskConical className="size-4" />
                Simulateur
              </Button>
            </>
          )}
        </div>
      </div>

      {showFilters && (
        <ValidationRuleFilters
          {...filters}
          activeFilterCount={activeFilterCount}
          search={search}
          onActiveFilterChange={(activeFilter: ActiveFilter) =>
            updateFilters({ activeFilter })
          }
          onDataTypeFilterChange={(dataTypeFilter) =>
            updateFilters({ dataTypeFilter })
          }
          onGenderFilterChange={(genderFilter) =>
            updateFilters({ genderFilter })
          }
          onAgeFilterChange={(ageFilter) => updateFilters({ ageFilter })}
          onAnalyteFilterChange={(analyteFilter, analyteFilterOption) =>
            updateFilters({ analyteFilter, analyteFilterOption })
          }
          onContextFilterChange={(contextFilter, contextFilterOption) =>
            updateFilters({ contextFilter, contextFilterOption })
          }
          onReset={resetFilters}
          loadAnalyteOptions={loadAnalyteOptions}
          loadContextOptions={loadContextOptions}
        />
      )}

      <ServerDataTable
        columns={columns}
        data={rows}
        loading={rulesQuery.isLoading}
        totalCount={totalCount}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          analyte_code: "analyte_code",
          priority: "priority",
          is_active: "is_active",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as SortBy)}
        emptyMessage="Aucune règle de validation trouvée."
        exportFilename="regles-validation.csv"
        exportColumns={validationRuleExportColumns}
      />

      <ValidationSimulatorSheet
        open={simulatorOpen}
        onOpenChange={setSimulatorOpen}
        loadAnalyteOptions={loadAnalyteOptions}
        loadContextOptions={loadContextOptions}
      />

      <ValidationRuleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        rule={dialogRule}
        loadAnalyteOptions={loadAnalyteOptions}
        loadContextOptions={loadContextOptions}
      />
    </div>
  )
}
