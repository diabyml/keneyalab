import { useQuery } from "@tanstack/react-query"
import { Download, Filter, RotateCcw, Search, ShieldCheck } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import {
  type ApiError,
  type AuditAction,
  type AuditCategory,
  AuditLogsService,
  type SortOrder,
} from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { AuditDetailSheet } from "./AuditDetailSheet"
import { getAuditColumns } from "./columns"
import {
  AUDIT_ACTION_LABELS,
  AUDIT_CATEGORY_LABELS,
  AUDIT_ENTITY_OPTIONS,
} from "./labels"

const ALL = "__all__"

export function AuditLogsView() {
  const { showErrorToast } = useCustomToast()
  const canExport = usePermission("audit", "export")
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [category, setCategory] = useState<AuditCategory | typeof ALL>(ALL)
  const [action, setAction] = useState<AuditAction | typeof ALL>(ALL)
  const [tableName, setTableName] = useState(ALL)
  const [actorId, setActorId] = useState<string | null>(null)
  const [actorOption, setActorOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [source, setSource] = useState(ALL)
  const [performedFrom, setPerformedFrom] = useState("")
  const [performedTo, setPerformedTo] = useState("")
  const [recordId, setRecordId] = useState("")
  const [requestId, setRequestId] = useState("")
  const [correlationId, setCorrelationId] = useState("")
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [sortBy, setSortBy] = useState("performed_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])

  const filters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      category: category === ALL ? undefined : category,
      action: action === ALL ? undefined : action,
      tableName: tableName === ALL ? undefined : tableName,
      performedById: actorId,
      source: source === ALL ? undefined : source,
      recordId: recordId || undefined,
      requestId: requestId || undefined,
      correlationId: correlationId || undefined,
      performedFrom: performedFrom
        ? new Date(`${performedFrom}T00:00:00`).toISOString()
        : undefined,
      performedTo: performedTo
        ? new Date(`${performedTo}T23:59:59.999`).toISOString()
        : undefined,
    }),
    [
      action,
      actorId,
      category,
      correlationId,
      debouncedSearch,
      performedFrom,
      performedTo,
      recordId,
      requestId,
      source,
      tableName,
    ],
  )

  const logsQuery = useQuery({
    queryKey: ["audit-logs", { ...filters, page, pageSize, sortBy, sortOrder }],
    queryFn: () =>
      AuditLogsService.readAuditLogs({
        ...filters,
        skip: page * pageSize,
        limit: pageSize,
        sortBy,
        sortOrder,
      }),
  })
  const summaryQuery = useQuery({
    queryKey: ["audit-summary", filters],
    queryFn: () => AuditLogsService.readAuditSummary(filters),
  })
  const columns = useMemo(() => getAuditColumns(setSelectedId), [])
  const loadActors = useCallback(async (value: string) => {
    const response = await AuditLogsService.readAuditActors({
      search: value || undefined,
      limit: 20,
    })
    return response.data.map((actor) => ({
      value: actor.id,
      label: actor.name || actor.email || actor.id,
      description: actor.name ? actor.email || undefined : undefined,
    }))
  }, [])

  const resetFilters = () => {
    setSearch("")
    setDebouncedSearch("")
    setCategory(ALL)
    setAction(ALL)
    setTableName(ALL)
    setActorId(null)
    setActorOption(null)
    setSource(ALL)
    setPerformedFrom("")
    setPerformedTo("")
    setRecordId("")
    setRequestId("")
    setCorrelationId("")
    setPage(0)
  }

  const exportCsv = async () => {
    setExporting(true)
    try {
      const content = await AuditLogsService.exportAuditLogs(filters)
      const blob =
        content instanceof Blob
          ? content
          : new Blob(
              [typeof content === "string" ? content : String(content)],
              {
                type: "text/csv;charset=utf-8",
              },
            )
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `journal-audit-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    } finally {
      setExporting(false)
    }
  }

  const onSort = (key: string) => {
    if (key === sortBy) setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    else {
      setSortBy(key)
      setSortOrder("asc")
    }
    setPage(0)
  }
  const summary = summaryQuery.data
  const summaryCards = [
    ["Total", summary?.total ?? 0],
    ["Créations", summary?.inserts ?? 0],
    ["Modifications", summary?.updates ?? 0],
    ["Suppressions", summary?.deletes ?? 0],
    ["Sécurité", summary?.security_events ?? 0],
  ]

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight">
              Journal d'audit
            </h1>
          </div>
          <p className="mt-1 text-muted-foreground">
            Traçabilité immuable des changements et événements de sécurité
          </p>
        </div>
        {canExport && (
          <Button variant="outline" onClick={exportCsv} disabled={exporting}>
            <Download className="size-4" />
            {exporting ? "Export en cours…" : "Exporter CSV"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {summaryCards.map(([label, value]) => (
          <Card key={label} size="sm">
            <CardContent>
              <div className="text-xs text-muted-foreground">{label}</div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {value.toLocaleString("fr-FR")}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="space-y-3 rounded-lg border bg-card p-3">
        <div className="grid gap-2 xl:grid-cols-[minmax(240px,1fr)_180px_180px_220px]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => {
                setSearch(event.currentTarget.value)
                setPage(0)
              }}
              className="pl-9"
              placeholder="Entité, acteur, libellé, identifiant…"
            />
          </div>
          <Select
            value={category}
            onValueChange={(value) => {
              setCategory(value as AuditCategory | typeof ALL)
              setPage(0)
            }}
          >
            <SelectTrigger aria-label="Filtrer par catégorie">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Toutes les catégories</SelectItem>
              {Object.entries(AUDIT_CATEGORY_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={action}
            onValueChange={(value) => {
              setAction(value as AuditAction | typeof ALL)
              setPage(0)
            }}
          >
            <SelectTrigger aria-label="Filtrer par action">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Toutes les actions</SelectItem>
              {Object.entries(AUDIT_ACTION_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={tableName}
            onValueChange={(value) => {
              setTableName(value)
              setPage(0)
            }}
          >
            <SelectTrigger aria-label="Filtrer par entité">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Toutes les entités</SelectItem>
              {AUDIT_ENTITY_OPTIONS.map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[220px_160px_170px_170px_auto_auto]">
          <SearchSelect
            value={actorId}
            selectedOption={actorOption}
            onValueChange={(value, option) => {
              setActorId(value)
              setActorOption(option ?? null)
              setPage(0)
            }}
            loadOptions={loadActors}
            placeholder="Tous les acteurs"
            searchPlaceholder="Rechercher un acteur…"
          />
          <Select
            value={source}
            onValueChange={(value) => {
              setSource(value)
              setPage(0)
            }}
          >
            <SelectTrigger aria-label="Filtrer par source">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Toutes les sources</SelectItem>
              <SelectItem value="api">Application</SelectItem>
              <SelectItem value="system">Système</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="date"
            value={performedFrom}
            onChange={(event) => {
              setPerformedFrom(event.currentTarget.value)
              setPage(0)
            }}
            aria-label="Date de début"
          />
          <Input
            type="date"
            value={performedTo}
            onChange={(event) => {
              setPerformedTo(event.currentTarget.value)
              setPage(0)
            }}
            aria-label="Date de fin"
          />
          <Button
            variant="ghost"
            onClick={() => setAdvancedOpen((current) => !current)}
          >
            <Filter className="size-4" />
            Filtres avancés
          </Button>
          <Button variant="ghost" onClick={resetFilters}>
            <RotateCcw className="size-4" />
            Réinitialiser
          </Button>
        </div>

        {advancedOpen && (
          <div className="grid gap-2 border-t pt-3 md:grid-cols-3">
            <Input
              value={recordId}
              onChange={(event) => {
                setRecordId(event.currentTarget.value.trim())
                setPage(0)
              }}
              placeholder="UUID de l'enregistrement"
              aria-label="Identifiant de l'enregistrement"
            />
            <Input
              value={requestId}
              onChange={(event) => {
                setRequestId(event.currentTarget.value)
                setPage(0)
              }}
              placeholder="ID de requête"
            />
            <Input
              value={correlationId}
              onChange={(event) => {
                setCorrelationId(event.currentTarget.value)
                setPage(0)
              }}
              placeholder="ID de corrélation"
            />
          </div>
        )}
      </div>

      <ServerDataTable
        columns={columns}
        data={logsQuery.data?.data ?? []}
        loading={logsQuery.isLoading}
        totalCount={logsQuery.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          performed_at: "performed_at",
          action: "action",
          table_name: "table_name",
          actor_name: "actor_name",
          source: "source",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={onSort}
        enableSelection={false}
        emptyMessage="Aucun événement d'audit ne correspond aux filtres."
      />

      <AuditDetailSheet
        auditId={selectedId}
        onOpenChange={(open) => {
          if (!open) setSelectedId(null)
        }}
      />
    </div>
  )
}
