import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { SortOrder } from "@/client"
import {
  CatalogService,
  InsurancePricingsService,
  InsuranceProvidersService,
} from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { usePermission } from "@/hooks/usePermission"
import { formatPrice } from "@/lib/format"
import { getInsurancePricingColumns } from "./columns"
import { InsurancePricingDialog } from "./InsurancePricingDialog"
import { type InsurancePricingSortBy, pricingExportColumns } from "./utils"

export function InsurancePricingsView() {
  const queryClient = useQueryClient()
  const canManage = usePermission("finance", "manage")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [providerId, setProviderId] = useState<string | null>(null)
  const [providerOption, setProviderOption] =
    useState<SearchSelectOption | null>(null)
  const [catalogId, setCatalogId] = useState<string | null>(null)
  const [catalogOption, setCatalogOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [dialogProviderOption, setDialogProviderOption] =
    useState<SearchSelectOption | null>(null)
  const [dialogCatalogOption, setDialogCatalogOption] =
    useState<SearchSelectOption | null>(null)
  const [minPrice, setMinPrice] = useState("")
  const [maxPrice, setMaxPrice] = useState("")
  const [sortBy, setSortBy] = useState<InsurancePricingSortBy>("provider_name")
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc")
  const [showFilters, setShowFilters] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  const activeFilterCount =
    (providerId ? 1 : 0) +
    (catalogId ? 1 : 0) +
    (minPrice.trim() ? 1 : 0) +
    (maxPrice.trim() ? 1 : 0)

  const pricingQuery = useQuery({
    queryKey: [
      "insurance-pricings",
      {
        page,
        pageSize,
        search,
        providerId,
        catalogId,
        minPrice,
        maxPrice,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      InsurancePricingsService.readInsurancePricings({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        insuranceProviderId: providerId || undefined,
        catalogId: catalogId || undefined,
        minPrice: minPrice.trim().replace(",", ".") || undefined,
        maxPrice: maxPrice.trim().replace(",", ".") || undefined,
        sortBy,
        sortOrder,
      }),
  })

  const loadProviderOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await InsuranceProvidersService.readInsuranceProviders({
        search: query || undefined,
        limit: 20,
        includeDeleted: false,
        sortBy: "name",
      })
      return response.data.map((provider) => ({
        value: provider.id,
        label: provider.name,
      }))
    },
    [],
  )

  const loadCatalogOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await CatalogService.readCatalog({
        search: query || undefined,
        limit: 20,
        type: "item",
        includeDeleted: false,
        isOrderable: true,
        sortBy: "code",
      })
      return response.data.map((test) => ({
        value: test.id,
        label: `${test.code} · ${test.name}`,
        description: formatPrice(test.price),
      }))
    },
    [],
  )

  const columns = useMemo(
    () =>
      getInsurancePricingColumns(() => {
        queryClient.invalidateQueries({ queryKey: ["insurance-pricings"] })
      }),
    [queryClient],
  )

  const onSort = (nextSortBy: InsurancePricingSortBy) => {
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
    setProviderId(null)
    setProviderOption(null)
    setCatalogId(null)
    setCatalogOption(null)
    setMinPrice("")
    setMaxPrice("")
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
            placeholder="Rechercher assureur, code ou test…"
            className="pl-9"
            aria-label="Rechercher des tarifs assurance"
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
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" />
              Nouveau tarif
            </Button>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <div className="grid gap-1.5">
              <div className="text-xs font-medium text-muted-foreground">
                Assureur
              </div>
              <SearchSelect
                value={providerId}
                selectedOption={providerOption}
                onValueChange={(value, option) => {
                  setProviderId(value)
                  setProviderOption(option ?? null)
                  setPage(0)
                }}
                loadOptions={loadProviderOptions}
                placeholder="Tous les assureurs"
                searchPlaceholder="Rechercher un assureur…"
                emptyMessage="Aucun assureur"
              />
            </div>
            <div className="grid gap-1.5">
              <div className="text-xs font-medium text-muted-foreground">
                Test
              </div>
              <SearchSelect
                value={catalogId}
                selectedOption={catalogOption}
                onValueChange={(value, option) => {
                  setCatalogId(value)
                  setCatalogOption(option ?? null)
                  setPage(0)
                }}
                loadOptions={loadCatalogOptions}
                placeholder="Tous les tests"
                searchPlaceholder="Rechercher un test…"
                emptyMessage="Aucun test"
              />
            </div>
            <div className="grid gap-1.5">
              <label
                htmlFor="insurance-pricing-min"
                className="text-xs font-medium text-muted-foreground"
              >
                Prix min
              </label>
              <Input
                id="insurance-pricing-min"
                value={minPrice}
                onChange={(event) => {
                  setMinPrice(event.currentTarget.value)
                  setPage(0)
                }}
                inputMode="decimal"
                placeholder="0,00"
              />
            </div>
            <div className="grid gap-1.5">
              <label
                htmlFor="insurance-pricing-max"
                className="text-xs font-medium text-muted-foreground"
              >
                Prix max
              </label>
              <Input
                id="insurance-pricing-max"
                value={maxPrice}
                onChange={(event) => {
                  setMaxPrice(event.currentTarget.value)
                  setPage(0)
                }}
                inputMode="decimal"
                placeholder="0,00"
              />
            </div>
            <div className="flex items-end">
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
        </div>
      )}

      <ServerDataTable
        columns={columns}
        data={pricingQuery.data?.data ?? []}
        loading={pricingQuery.isLoading}
        totalCount={pricingQuery.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          provider_name: "provider_name",
          catalog_code: "catalog_code",
          catalog_name: "catalog_name",
          catalog_price: "catalog_price",
          insurance_price: "insurance_price",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as InsurancePricingSortBy)}
        emptyMessage="Aucun tarif assurance trouvé."
        exportFilename="tarifs-assurance.csv"
        exportColumns={pricingExportColumns()}
      />

      <InsurancePricingDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        pricing={null}
        providerOption={dialogProviderOption}
        catalogOption={dialogCatalogOption}
        onProviderOptionChange={setDialogProviderOption}
        onCatalogOptionChange={setDialogCatalogOption}
        loadProviderOptions={loadProviderOptions}
        loadCatalogOptions={loadCatalogOptions}
      />
    </div>
  )
}
