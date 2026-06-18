import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { AlertTriangle, Search } from "lucide-react"
import { useMemo, useState } from "react"

import type {
  CriticalNotificationDetailPublic,
  ResultQueueItemPublic,
  SortOrder,
} from "@/client"
import { CriticalNotificationsService, ResultsService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { usePermission } from "@/hooks/usePermission"

type ResultsTab = "entry" | "verification" | "critical"

export function ResultsView() {
  const canVerify = usePermission("results", "verify")
  const canViewCritical = usePermission("critical_notifications", "view")
  const [tab, setTab] = useState<ResultsTab>("entry")

  return (
    <Tabs value={tab} onValueChange={(value) => setTab(value as ResultsTab)}>
      <TabsList>
        <TabsTrigger value="entry">Saisie</TabsTrigger>
        {canVerify && (
          <TabsTrigger value="verification">Vérification</TabsTrigger>
        )}
        {canViewCritical && (
          <TabsTrigger value="critical">Valeurs critiques</TabsTrigger>
        )}
      </TabsList>
      <TabsContent value="entry" className="mt-4">
        <ResultsQueue mode="entry" />
      </TabsContent>
      <TabsContent value="verification" className="mt-4">
        <ResultsQueue mode="verification" />
      </TabsContent>
      <TabsContent value="critical" className="mt-4">
        <CriticalQueue />
      </TabsContent>
    </Tabs>
  )
}

function ResultsQueue({ mode }: { mode: "entry" | "verification" }) {
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const query = useQuery({
    queryKey: ["result-queue", { mode, search, page, pageSize, sortOrder }],
    queryFn: () =>
      ResultsService.readResultQueue({
        mode,
        search: search.trim() || undefined,
        skip: page * pageSize,
        limit: pageSize,
        sortOrder,
      }),
  })
  const columns = useMemo<ColumnDef<ResultQueueItemPublic>[]>(
    () => [
      {
        accessorKey: "accession_number",
        header: "Demande",
        cell: ({ row }) => (
          <Link
            to="/results/$orderId"
            params={{ orderId: row.original.order_id }}
            className="font-mono font-medium text-primary hover:underline"
          >
            {row.original.accession_number}
          </Link>
        ),
      },
      {
        accessorKey: "patient_name",
        header: "Patient",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.patient_name}</div>
            <div className="text-xs text-muted-foreground">
              {row.original.patient_identifier}
            </div>
          </div>
        ),
      },
      { accessorKey: "category_summary", header: "Disciplines" },
      {
        id: "progress",
        header: "Progression",
        cell: ({ row }) => {
          const completed =
            mode === "verification"
              ? row.original.verified_count
              : row.original.resulted_count
          const percent = row.original.total_count
            ? (completed / row.original.total_count) * 100
            : 0
          return (
            <div className="w-40 space-y-1">
              <Progress value={percent} className="h-2" />
              <div className="text-xs text-muted-foreground">
                {completed}/{row.original.total_count}
              </div>
            </div>
          )
        },
      },
      {
        id: "flags",
        header: "Alertes",
        cell: ({ row }) => (
          <div className="flex gap-1">
            {row.original.abnormal_count > 0 && (
              <Badge variant="outline">
                {row.original.abnormal_count} anormal
              </Badge>
            )}
            {row.original.critical_count > 0 && (
              <Badge variant="destructive">
                {row.original.critical_count} critique
              </Badge>
            )}
          </div>
        ),
      },
      {
        id: "action",
        header: "",
        cell: ({ row }) => (
          <Button size="sm" asChild>
            <Link
              to="/results/$orderId"
              params={{ orderId: row.original.order_id }}
            >
              {mode === "verification" ? "Examiner" : "Saisir"}
            </Link>
          </Button>
        ),
      },
    ],
    [mode],
  )

  return (
    <div className="space-y-4">
      <div className="relative max-w-xl">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.currentTarget.value)
            setPage(0)
          }}
          className="pl-9"
          placeholder="N° demande, patient, identifiant…"
        />
      </div>
      <ServerDataTable
        columns={columns}
        data={query.data?.data ?? []}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy="created_at"
        sortOrder={sortOrder}
        sortableColumns={{ created_at: "created_at" }}
        onSortChange={() =>
          setSortOrder((current) => (current === "asc" ? "desc" : "asc"))
        }
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        enableSelection={false}
        getRowId={(row) => row.order_id}
        emptyMessage={
          mode === "verification"
            ? "Aucun résultat à vérifier."
            : "Aucune demande prête pour la saisie."
        }
      />
    </div>
  )
}

function CriticalQueue() {
  const queryClient = useQueryClient()
  const canAcknowledge = usePermission("critical_notifications", "acknowledge")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const query = useQuery({
    queryKey: ["critical-notifications", { search, page, pageSize }],
    queryFn: () =>
      CriticalNotificationsService.readCriticalNotifications({
        search: search.trim() || undefined,
        skip: page * pageSize,
        limit: pageSize,
      }),
  })
  const acknowledgeMutation = useMutation({
    mutationFn: (notificationId: string) =>
      CriticalNotificationsService.acknowledgeCriticalNotification({
        notificationId,
        requestBody: {},
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["critical-notifications"] })
      queryClient.invalidateQueries({ queryKey: ["result-workspace"] })
    },
  })
  const columns = useMemo<ColumnDef<CriticalNotificationDetailPublic>[]>(
    () => [
      { accessorKey: "accession_number", header: "Demande" },
      { accessorKey: "patient_name", header: "Patient" },
      {
        accessorKey: "analyte_name",
        header: "Analyte",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.analyte_name}</div>
            <div className="text-xs text-muted-foreground">
              {row.original.analyte_code}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "result_value",
        header: "Valeur",
        cell: ({ row }) => (
          <span className="font-mono font-semibold text-destructive">
            {row.original.result_value}
          </span>
        ),
      },
      { accessorKey: "notified_to_name", header: "Destinataire" },
      {
        accessorKey: "acknowledged",
        header: "Statut",
        cell: ({ row }) =>
          row.original.acknowledged ? (
            <Badge variant="outline">Acquittée</Badge>
          ) : (
            <Badge variant="destructive">
              <AlertTriangle className="size-3" />À acquitter
            </Badge>
          ),
      },
      {
        id: "action",
        header: "",
        cell: ({ row }) =>
          canAcknowledge && !row.original.acknowledged ? (
            <Button
              size="sm"
              variant="outline"
              disabled={acknowledgeMutation.isPending}
              onClick={() => acknowledgeMutation.mutate(row.original.id)}
            >
              Acquitter
            </Button>
          ) : null,
      },
    ],
    [acknowledgeMutation, canAcknowledge],
  )
  return (
    <div className="space-y-4">
      <div className="relative max-w-xl">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.currentTarget.value)
            setPage(0)
          }}
          className="pl-9"
          placeholder="Demande, patient ou analyte…"
        />
      </div>
      <ServerDataTable
        columns={columns}
        data={query.data?.data ?? []}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        enableSelection={false}
        getRowId={(row) => row.id}
        emptyMessage="Aucune notification critique."
      />
    </div>
  )
}
