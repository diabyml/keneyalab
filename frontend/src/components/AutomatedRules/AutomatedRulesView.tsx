import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type {
  ConsistencyRuleDetailPublic,
  ReflexRuleDetailPublic,
  RuleSeverity,
  SortOrder,
  TriggerOperator,
} from "@/client"
import {
  AnalytesService,
  AutomatedRulesService,
  CatalogService,
} from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import {
  ConsistencyFilters,
  type OperatorFilter,
  ReflexFilters,
  type SeverityFilter,
  type StatusFilter,
} from "./AutomatedRuleFilters"
import { AutomatedRulePreviewSheet } from "./AutomatedRulePreviewSheet"
import { ConsistencyRuleDialog } from "./ConsistencyRuleDialog"
import {
  consistencyExportColumns,
  getConsistencyColumns,
  getReflexColumns,
  reflexExportColumns,
} from "./columns"
import { ReflexRuleDialog } from "./ReflexRuleDialog"

type TabValue = "consistency" | "reflex"
type PreviewTarget =
  | { type: "consistency"; rule: ConsistencyRuleDetailPublic }
  | { type: "reflex"; rule: ReflexRuleDetailPublic }
  | null

export function AutomatedRulesView() {
  const canManage = usePermission("rules", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [tab, setTab] = useState<TabValue>("consistency")
  const [search, setSearch] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [consistencyPage, setConsistencyPage] = useState(0)
  const [reflexPage, setReflexPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [consistencySortBy, setConsistencySortBy] = useState("name")
  const [reflexSortBy, setReflexSortBy] = useState("trigger_analyte")
  const [consistencySortOrder, setConsistencySortOrder] =
    useState<SortOrder>("asc")
  const [reflexSortOrder, setReflexSortOrder] = useState<SortOrder>("asc")
  const [status, setStatus] = useState<StatusFilter>("active")
  const [severity, setSeverity] = useState<SeverityFilter>("all")
  const [operator, setOperator] = useState<OperatorFilter>("all")
  const [analyteFilter, setAnalyteFilter] = useState<SearchSelectOption | null>(
    null,
  )
  const [actionFilter, setActionFilter] = useState<SearchSelectOption | null>(
    null,
  )
  const [consistencyDialogRule, setConsistencyDialogRule] =
    useState<ConsistencyRuleDetailPublic | null>(null)
  const [consistencyDialogOpen, setConsistencyDialogOpen] = useState(false)
  const [reflexDialogRule, setReflexDialogRule] =
    useState<ReflexRuleDetailPublic | null>(null)
  const [reflexDialogOpen, setReflexDialogOpen] = useState(false)
  const [previewTarget, setPreviewTarget] = useState<PreviewTarget>(null)

  const loadAnalyteOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await AnalytesService.readAnalytes({
        search: query || undefined,
        dataType: "numeric",
        limit: 20,
      })
      return response.data.map((analyte) => ({
        value: analyte.id,
        label: `${analyte.code} - ${analyte.name}`,
        description: `${analyte.code} · ${analyte.name}`,
      }))
    },
    [],
  )

  const loadCatalogOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await CatalogService.readCatalog({
        search: query || undefined,
        limit: 20,
        includeDeleted: false,
      })
      return response.data.map((item) => ({
        value: item.id,
        label: `${item.code} - ${item.name}`,
        description: item.type === "panel" ? "Panel" : "Test",
      }))
    },
    [],
  )

  const consistencyQuery = useQuery({
    queryKey: [
      "automated-rules",
      "consistency",
      search,
      consistencyPage,
      pageSize,
      consistencySortBy,
      consistencySortOrder,
      status,
      severity,
      analyteFilter?.value,
    ],
    queryFn: () =>
      AutomatedRulesService.readConsistencyRules({
        skip: consistencyPage * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: status !== "active" || undefined,
        isDeleted: status === "all" ? undefined : status === "deleted",
        severity: severity === "all" ? undefined : (severity as RuleSeverity),
        analyteId: analyteFilter?.value,
        sortBy: consistencySortBy,
        sortOrder: consistencySortOrder,
      }),
  })

  const reflexQuery = useQuery({
    queryKey: [
      "automated-rules",
      "reflex",
      search,
      reflexPage,
      pageSize,
      reflexSortBy,
      reflexSortOrder,
      status,
      operator,
      analyteFilter?.value,
      actionFilter?.value,
    ],
    queryFn: () =>
      AutomatedRulesService.readReflexRules({
        skip: reflexPage * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: status !== "active" || undefined,
        isDeleted: status === "all" ? undefined : status === "deleted",
        triggerOperator:
          operator === "all" ? undefined : (operator as TriggerOperator),
        triggerAnalyteId: analyteFilter?.value,
        actionCatalogId: actionFilter?.value,
        sortBy: reflexSortBy,
        sortOrder: reflexSortOrder,
      }),
  })

  const deleteConsistencyMutation = useMutation({
    mutationFn: (rule: ConsistencyRuleDetailPublic) =>
      AutomatedRulesService.deleteConsistencyRule({ id: rule.id }),
    onSuccess: () => showSuccessToast("Règle de cohérence supprimée"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })
  const restoreConsistencyMutation = useMutation({
    mutationFn: (rule: ConsistencyRuleDetailPublic) =>
      AutomatedRulesService.restoreConsistencyRule({ id: rule.id }),
    onSuccess: () => showSuccessToast("Règle de cohérence restaurée"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })
  const deleteReflexMutation = useMutation({
    mutationFn: (rule: ReflexRuleDetailPublic) =>
      AutomatedRulesService.deleteReflexRule({ id: rule.id }),
    onSuccess: () => showSuccessToast("Règle réflexe supprimée"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })
  const restoreReflexMutation = useMutation({
    mutationFn: (rule: ReflexRuleDetailPublic) =>
      AutomatedRulesService.restoreReflexRule({ id: rule.id }),
    onSuccess: () => showSuccessToast("Règle réflexe restaurée"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })

  const consistencyColumns = useMemo(
    () =>
      getConsistencyColumns({
        onEdit: (rule) => {
          setConsistencyDialogRule(rule)
          setConsistencyDialogOpen(true)
        },
        onPreview: (rule) => setPreviewTarget({ type: "consistency", rule }),
        onDelete: (rule) => deleteConsistencyMutation.mutate(rule),
        onRestore: (rule) => restoreConsistencyMutation.mutate(rule),
      }),
    [deleteConsistencyMutation, restoreConsistencyMutation],
  )
  const reflexColumns = useMemo(
    () =>
      getReflexColumns({
        onEdit: (rule) => {
          setReflexDialogRule(rule)
          setReflexDialogOpen(true)
        },
        onPreview: (rule) => setPreviewTarget({ type: "reflex", rule }),
        onDelete: (rule) => deleteReflexMutation.mutate(rule),
        onRestore: (rule) => restoreReflexMutation.mutate(rule),
      }),
    [deleteReflexMutation, restoreReflexMutation],
  )

  const resetFilters = () => {
    setSearch("")
    setStatus("active")
    setSeverity("all")
    setOperator("all")
    setAnalyteFilter(null)
    setActionFilter(null)
    setConsistencyPage(0)
    setReflexPage(0)
  }

  const onConsistencySort = (nextSortBy: string) => {
    setConsistencySortOrder(
      consistencySortBy === nextSortBy && consistencySortOrder === "asc"
        ? "desc"
        : "asc",
    )
    setConsistencySortBy(nextSortBy)
    setConsistencyPage(0)
  }

  const onReflexSort = (nextSortBy: string) => {
    setReflexSortOrder(
      reflexSortBy === nextSortBy && reflexSortOrder === "asc" ? "desc" : "asc",
    )
    setReflexSortBy(nextSortBy)
    setReflexPage(0)
  }

  const activeFilterCount =
    (status !== "active" ? 1 : 0) +
    (severity !== "all" && tab === "consistency" ? 1 : 0) +
    (operator !== "all" && tab === "reflex" ? 1 : 0) +
    (analyteFilter ? 1 : 0) +
    (actionFilter && tab === "reflex" ? 1 : 0)

  return (
    <div className="flex flex-col gap-4">
      <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <TabsList>
            <TabsTrigger value="consistency">Cohérence</TabsTrigger>
            <TabsTrigger value="reflex">Réflexes</TabsTrigger>
          </TabsList>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-full sm:w-72">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => {
                  setSearch(event.currentTarget.value)
                  setConsistencyPage(0)
                  setReflexPage(0)
                }}
                placeholder={
                  tab === "consistency"
                    ? "Rechercher une règle…"
                    : "Rechercher analyte ou action…"
                }
                className="pl-9"
              />
            </div>
            <Button
              variant={showFilters ? "secondary" : "outline"}
              size="sm"
              onClick={() => setShowFilters((value) => !value)}
            >
              <SlidersHorizontal className="size-4" />
              Filtres
              {activeFilterCount > 0 && <Badge>{activeFilterCount}</Badge>}
            </Button>
            {canManage && (
              <Button
                onClick={() => {
                  if (tab === "consistency") {
                    setConsistencyDialogRule(null)
                    setConsistencyDialogOpen(true)
                  } else {
                    setReflexDialogRule(null)
                    setReflexDialogOpen(true)
                  }
                }}
              >
                <Plus className="size-4" />
                Ajouter
              </Button>
            )}
          </div>
        </div>

        {showFilters && tab === "consistency" && (
          <ConsistencyFilters
            status={status}
            severity={severity}
            analyteId={analyteFilter?.value ?? null}
            analyteOption={analyteFilter}
            onStatusChange={(value) => {
              setStatus(value)
              setConsistencyPage(0)
            }}
            onSeverityChange={(value) => {
              setSeverity(value)
              setConsistencyPage(0)
            }}
            onAnalyteChange={(_value, option) => {
              setAnalyteFilter(option ?? null)
              setConsistencyPage(0)
            }}
            onReset={resetFilters}
            loadAnalyteOptions={loadAnalyteOptions}
          />
        )}
        {showFilters && tab === "reflex" && (
          <ReflexFilters
            status={status}
            operator={operator}
            triggerAnalyteId={analyteFilter?.value ?? null}
            triggerAnalyteOption={analyteFilter}
            actionCatalogId={actionFilter?.value ?? null}
            actionCatalogOption={actionFilter}
            onStatusChange={(value) => {
              setStatus(value)
              setReflexPage(0)
            }}
            onOperatorChange={(value) => {
              setOperator(value)
              setReflexPage(0)
            }}
            onTriggerAnalyteChange={(_value, option) => {
              setAnalyteFilter(option ?? null)
              setReflexPage(0)
            }}
            onActionCatalogChange={(_value, option) => {
              setActionFilter(option ?? null)
              setReflexPage(0)
            }}
            onReset={resetFilters}
            loadAnalyteOptions={loadAnalyteOptions}
            loadCatalogOptions={loadCatalogOptions}
          />
        )}

        <TabsContent value="consistency" className="mt-4">
          <ServerDataTable
            columns={consistencyColumns}
            data={consistencyQuery.data?.data ?? []}
            loading={consistencyQuery.isLoading}
            totalCount={consistencyQuery.data?.count ?? 0}
            page={consistencyPage}
            pageSize={pageSize}
            sortBy={consistencySortBy}
            sortOrder={consistencySortOrder}
            sortableColumns={{
              name: "name",
              severity: "severity",
              is_deleted: "created_at",
            }}
            onPageChange={setConsistencyPage}
            onPageSizeChange={(value) => {
              setPageSize(value)
              setConsistencyPage(0)
            }}
            onSortChange={onConsistencySort}
            emptyMessage="Aucune règle de cohérence trouvée."
            exportFilename="regles-coherence.csv"
            exportColumns={consistencyExportColumns}
          />
        </TabsContent>
        <TabsContent value="reflex" className="mt-4">
          <ServerDataTable
            columns={reflexColumns}
            data={reflexQuery.data?.data ?? []}
            loading={reflexQuery.isLoading}
            totalCount={reflexQuery.data?.count ?? 0}
            page={reflexPage}
            pageSize={pageSize}
            sortBy={reflexSortBy}
            sortOrder={reflexSortOrder}
            sortableColumns={{
              trigger_analyte: "trigger_analyte",
              trigger_operator: "trigger_operator",
              action_catalog: "action_catalog",
            }}
            onPageChange={setReflexPage}
            onPageSizeChange={(value) => {
              setPageSize(value)
              setReflexPage(0)
            }}
            onSortChange={onReflexSort}
            emptyMessage="Aucune règle réflexe trouvée."
            exportFilename="regles-reflexes.csv"
            exportColumns={reflexExportColumns}
          />
        </TabsContent>
      </Tabs>

      <ConsistencyRuleDialog
        open={consistencyDialogOpen}
        onOpenChange={setConsistencyDialogOpen}
        rule={consistencyDialogRule}
        loadAnalyteOptions={loadAnalyteOptions}
      />
      <ReflexRuleDialog
        open={reflexDialogOpen}
        onOpenChange={setReflexDialogOpen}
        rule={reflexDialogRule}
        loadAnalyteOptions={loadAnalyteOptions}
        loadCatalogOptions={loadCatalogOptions}
      />
      <AutomatedRulePreviewSheet
        target={previewTarget}
        onOpenChange={(open) => !open && setPreviewTarget(null)}
      />
    </div>
  )
}
