import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { PanelTop, Plus, Search, SlidersHorizontal } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type { CatalogType, SortOrder } from "@/client"
import { CatalogService, CategoriesService } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { CatalogueDetailSheet } from "./CatalogueDetailSheet"
import { CatalogueDialog } from "./CatalogueDialog"
import { CatalogueFilters } from "./CatalogueFilters"
import { catalogExportColumns, getCatalogColumns } from "./columns"
import {
  ALL,
  type CatalogFilterState,
  type OrderableFilter,
  type SortBy,
  type StatusFilter,
} from "./types"
import { getCatalogQueryKey, initialCatalogFilters } from "./utils"

export function CatalogueView() {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [filters, setFilters] = useState<CatalogFilterState>(
    initialCatalogFilters,
  )
  const [sortBy, setSortBy] = useState<SortBy>("code")
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc")
  const [showFilters, setShowFilters] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [createType, setCreateType] = useState<CatalogType | null>(null)

  const activeFilterCount =
    (filters.statusFilter !== "active" ? 1 : 0) +
    (filters.typeFilter !== ALL ? 1 : 0) +
    (filters.categoryFilter !== ALL ? 1 : 0) +
    (filters.orderableFilter !== "all" ? 1 : 0)

  const catalogQueryParams = {
    page,
    pageSize,
    search,
    sortBy,
    sortOrder,
    ...filters,
  }

  const catalogQuery = useQuery({
    queryKey: getCatalogQueryKey(catalogQueryParams),
    queryFn: () =>
      CatalogService.readCatalog({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: filters.statusFilter !== "active" || undefined,
        isDeleted:
          filters.statusFilter === "all"
            ? undefined
            : filters.statusFilter === "deleted",
        type:
          filters.typeFilter === ALL
            ? undefined
            : (filters.typeFilter as CatalogType),
        categoryId:
          filters.categoryFilter === ALL ? undefined : filters.categoryFilter,
        isOrderable:
          filters.orderableFilter === "all"
            ? undefined
            : filters.orderableFilter === "yes",
        sortBy,
        sortOrder,
      }),
  })

  const rows = catalogQuery.data?.data ?? []
  const totalCount = catalogQuery.data?.count ?? 0
  const columns = useMemo(() => getCatalogColumns(setSelectedId), [])

  const loadCategoryOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await CategoriesService.readCategories({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((category) => ({
        value: category.id,
        label: category.name,
      }))
    },
    [],
  )

  useEffect(() => {
    if (
      selectedId &&
      rows.length > 0 &&
      !rows.some((row) => row.id === selectedId)
    ) {
      setSelectedId(null)
    }
  }, [rows, selectedId])

  const deleteMutation = useMutation({
    mutationFn: (id: string) => CatalogService.deleteCatalog({ id }),
    onSuccess: () => {
      showSuccessToast("Entrée catalogue supprimée")
      setSelectedId(null)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["catalog"] })
    },
  })

  const restoreMutation = useMutation({
    mutationFn: (id: string) => CatalogService.restoreCatalog({ id }),
    onSuccess: () => {
      showSuccessToast("Entrée catalogue restaurée")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["catalog"] })
    },
  })

  const updateFilters = (next: Partial<CatalogFilterState>) => {
    setFilters((current) => ({ ...current, ...next }))
    setPage(0)
  }

  const resetFilters = () => {
    setSearch("")
    setFilters(initialCatalogFilters())
    setPage(0)
  }

  const onSort = (nextSortBy: SortBy) => {
    if (sortBy === nextSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(nextSortBy)
      setSortOrder("asc")
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
            placeholder="Rechercher code ou nom…"
            className="pl-9"
            aria-label="Rechercher dans le catalogue"
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
              <Button variant="outline" onClick={() => setCreateType("panel")}>
                <PanelTop className="size-4" />
                Ajouter un panel
              </Button>
              <Button onClick={() => setCreateType("item")}>
                <Plus className="size-4" />
                Ajouter un test
              </Button>
            </>
          )}
        </div>
      </div>

      {showFilters && (
        <CatalogueFilters
          {...filters}
          activeFilterCount={activeFilterCount}
          search={search}
          onStatusFilterChange={(statusFilter: StatusFilter) =>
            updateFilters({ statusFilter })
          }
          onTypeFilterChange={(typeFilter) => updateFilters({ typeFilter })}
          onCategoryFilterChange={(categoryFilter, categoryFilterOption) =>
            updateFilters({ categoryFilter, categoryFilterOption })
          }
          onOrderableFilterChange={(orderableFilter: OrderableFilter) =>
            updateFilters({ orderableFilter })
          }
          onReset={resetFilters}
          loadCategoryOptions={loadCategoryOptions}
        />
      )}

      <ServerDataTable
        columns={columns}
        data={rows}
        loading={catalogQuery.isLoading}
        totalCount={totalCount}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          code: "code",
          name: "name",
          type: "type",
          price: "price",
          is_orderable: "is_orderable",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as SortBy)}
        emptyMessage="Aucune entrée catalogue trouvée."
        getRowClassName={(row) =>
          selectedId === row.id ? "bg-accent hover:bg-accent" : undefined
        }
        exportFilename="catalogue.csv"
        exportColumns={catalogExportColumns}
      />

      <CatalogueDetailSheet
        selectedId={selectedId}
        onOpenChange={(open) => {
          if (!open) setSelectedId(null)
        }}
        onDelete={(id) => deleteMutation.mutate(id)}
        onRestore={(id) => restoreMutation.mutate(id)}
        loadCategoryOptions={loadCategoryOptions}
      />

      <CatalogueDialog
        open={createType !== null}
        onOpenChange={(open) => !open && setCreateType(null)}
        type={createType ?? "item"}
        onCreated={(id) => {
          setSelectedId(id)
          setCreateType(null)
        }}
        loadCategoryOptions={loadCategoryOptions}
      />
    </div>
  )
}
