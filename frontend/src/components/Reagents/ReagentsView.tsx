import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { ColumnDef } from "@tanstack/react-table"
import {
  AlertTriangle,
  ArchiveRestore,
  Boxes,
  CalendarClock,
  Eye,
  PackagePlus,
  Plus,
  RotateCcw,
  Settings,
  SlidersHorizontal,
  Trash2,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import type {
  ReagentExpiryStatus,
  ReagentLotPublic,
  ReagentMovementType,
  ReagentPublic,
} from "@/client"
import { ReagentsService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import type { ExportColumn } from "@/components/Common/tableExport"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"

type StatusFilter = "active" | "deleted" | "all"
type StockFilter = "all" | "low" | "ok"
type ExpiryFilter = "all" | ReagentExpiryStatus

const QUERY_KEY = ["reagents"] as const
const today = new Date().toISOString().slice(0, 10)

function numberValue(value: string | null | undefined) {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function quantity(
  value: string | number | null | undefined,
  unit?: string | null,
) {
  return `${Number(value ?? 0).toLocaleString("fr-FR", {
    maximumFractionDigits: 3,
  })} ${unit ?? ""}`.trim()
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value))
}

function expiryLabel(status?: ReagentExpiryStatus) {
  if (status === "expired") return "Expiré"
  if (status === "expiring") return "Bientôt expiré"
  return "OK"
}

function expiryTone(status?: ReagentExpiryStatus) {
  if (status === "expired") return "destructive"
  if (status === "expiring") return "outline"
  return "secondary"
}

function movementLabel(type: ReagentMovementType) {
  const labels: Record<ReagentMovementType, string> = {
    received: "Réception",
    used: "Utilisation",
    adjusted: "Ajustement",
    disposed: "Élimination",
  }
  return labels[type]
}

export function ReagentsView() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const canManage = usePermission("reagents", "manage")
  const canRecord = usePermission("reagents", "record_movement")
  const canManageSettings = usePermission("reagents", "manage_settings")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [stockFilter, setStockFilter] = useState<StockFilter>("all")
  const [expiryFilter, setExpiryFilter] = useState<ExpiryFilter>("all")
  const [showFilters, setShowFilters] = useState(false)
  const [selected, setSelected] = useState<ReagentPublic | null>(null)
  const [editing, setEditing] = useState<ReagentPublic | null | "new">(null)
  const [receiving, setReceiving] = useState<ReagentPublic | null>(null)
  const [movementLot, setMovementLot] = useState<ReagentLotPublic | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const query = useQuery({
    queryKey: [
      ...QUERY_KEY,
      { search, page, pageSize, statusFilter, stockFilter, expiryFilter },
    ],
    queryFn: () =>
      ReagentsService.readReagents({
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        includeDeleted: statusFilter !== "active" || undefined,
        isDeleted:
          statusFilter === "all" ? undefined : statusFilter === "deleted",
        stockStatus: stockFilter === "all" ? undefined : stockFilter,
        expiryStatus: expiryFilter === "all" ? undefined : expiryFilter,
      }),
  })
  const summaryQuery = useQuery({
    queryKey: [...QUERY_KEY, "alert-summary"],
    queryFn: () => ReagentsService.readReagentAlertSummary(),
    refetchInterval: 30_000,
  })

  const rows = query.data?.data ?? []
  const columns = useMemo(
    () => getColumns((row) => setSelected(row), canManage, canRecord),
    [canManage, canRecord],
  )

  useEffect(() => {
    if (selected && rows.length > 0) {
      const fresh = rows.find((row) => row.id === selected.id)
      if (fresh) setSelected(fresh)
    }
  }, [rows, selected])

  const deleteMutation = useMutation({
    mutationFn: (reagentId: string) =>
      ReagentsService.deleteReagent({ reagentId }),
    onSuccess: () => showSuccessToast("Réactif supprimé"),
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })
  const restoreMutation = useMutation({
    mutationFn: (reagentId: string) =>
      ReagentsService.restoreReagent({ reagentId }),
    onSuccess: () => showSuccessToast("Réactif restauré"),
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  const resetFilters = () => {
    setSearch("")
    setStatusFilter("active")
    setStockFilter("all")
    setExpiryFilter("all")
    setPage(0)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard
          icon={AlertTriangle}
          label="Alertes"
          value={summaryQuery.data?.total_count ?? 0}
        />
        <MetricCard
          icon={CalendarClock}
          label="Bientôt expirés"
          value={summaryQuery.data?.expiring_count ?? 0}
        />
        <MetricCard
          icon={AlertTriangle}
          label="Expirés"
          value={summaryQuery.data?.expired_count ?? 0}
          destructive
        />
        <MetricCard
          icon={Boxes}
          label="Stock bas"
          value={summaryQuery.data?.low_stock_count ?? 0}
        />
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex w-full flex-col gap-2 sm:flex-row lg:max-w-xl">
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            placeholder="Rechercher code, nom ou fournisseur…"
            aria-label="Rechercher des réactifs"
          />
          <Button
            variant={showFilters ? "secondary" : "outline"}
            onClick={() => setShowFilters((value) => !value)}
          >
            <SlidersHorizontal className="size-4" />
            Filtres
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {canManageSettings && (
            <Button variant="outline" onClick={() => setSettingsOpen(true)}>
              <Settings className="size-4" />
              Réglages
            </Button>
          )}
          {canManage && (
            <Button onClick={() => setEditing("new")}>
              <Plus className="size-4" />
              Ajouter un réactif
            </Button>
          )}
        </div>
      </div>

      {showFilters && (
        <Card className="rounded-lg py-4 shadow-none">
          <CardContent className="flex flex-wrap items-end gap-4">
            <FilterSelect
              label="Statut"
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value as StatusFilter)
                setPage(0)
              }}
              options={[
                ["active", "Actifs"],
                ["deleted", "Supprimés"],
                ["all", "Tous"],
              ]}
            />
            <FilterSelect
              label="Stock"
              value={stockFilter}
              onValueChange={(value) => {
                setStockFilter(value as StockFilter)
                setPage(0)
              }}
              options={[
                ["all", "Tous"],
                ["low", "Stock bas"],
                ["ok", "OK"],
              ]}
            />
            <FilterSelect
              label="Expiration"
              value={expiryFilter}
              onValueChange={(value) => {
                setExpiryFilter(value as ExpiryFilter)
                setPage(0)
              }}
              options={[
                ["all", "Toutes"],
                ["expiring", "Bientôt expirés"],
                ["expired", "Expirés"],
                ["ok", "OK"],
              ]}
            />
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              <RotateCcw className="size-4" />
              Réinitialiser
            </Button>
          </CardContent>
        </Card>
      )}

      <ServerDataTable
        columns={columns}
        data={rows}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        emptyMessage="Aucun réactif trouvé."
        exportFilename="reactifs.csv"
        exportColumns={exportColumns}
      />

      <ReagentDetailSheet
        reagent={selected}
        canManage={canManage}
        canRecord={canRecord}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
        onEdit={setEditing}
        onReceive={setReceiving}
        onMovement={setMovementLot}
        onDelete={(reagent) => deleteMutation.mutate(reagent.id)}
        onRestore={(reagent) => restoreMutation.mutate(reagent.id)}
      />
      <ReagentDialog reagent={editing} onOpenChange={() => setEditing(null)} />
      <ReceiveLotDialog
        reagent={receiving}
        onOpenChange={() => setReceiving(null)}
      />
      <MovementDialog
        lot={movementLot}
        onOpenChange={() => setMovementLot(null)}
      />
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  )
}

function getColumns(
  onSelect: (row: ReagentPublic) => void,
  canManage: boolean,
  canRecord: boolean,
): ColumnDef<ReagentPublic>[] {
  return [
    {
      accessorKey: "code",
      header: "Code",
      cell: ({ row }) => (
        <span className="font-medium">{row.original.code}</span>
      ),
    },
    { accessorKey: "name", header: "Nom" },
    {
      accessorKey: "total_stock",
      header: "Stock",
      cell: ({ row }) =>
        quantity(row.original.total_stock, row.original.unit_label),
    },
    {
      accessorKey: "supplier",
      header: "Fournisseur",
      cell: ({ row }) => row.original.supplier ?? "—",
    },
    {
      id: "alerts",
      header: "Alertes",
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.low_stock && <Badge variant="outline">Stock bas</Badge>}
          {!!row.original.expiring_lot_count && (
            <Badge variant="outline">
              {row.original.expiring_lot_count} bientôt
            </Badge>
          )}
          {!!row.original.expired_lot_count && (
            <Badge variant="destructive">
              {row.original.expired_lot_count} expiré
            </Badge>
          )}
          {!row.original.low_stock &&
            !row.original.expiring_lot_count &&
            !row.original.expired_lot_count && (
              <Badge variant="secondary">OK</Badge>
            )}
        </div>
      ),
    },
    {
      accessorKey: "is_deleted",
      header: "Statut",
      cell: ({ row }) => (
        <Badge variant={row.original.is_deleted ? "outline" : "secondary"}>
          {row.original.is_deleted ? "Supprimé" : "Actif"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => onSelect(row.original)}
            disabled={!canManage && !canRecord}
          >
            <Eye className="size-4" />
            <span className="sr-only">Afficher {row.original.name}</span>
          </Button>
        </div>
      ),
    },
  ]
}

const exportColumns: ExportColumn<ReagentPublic>[] = [
  { header: "Code", value: (row) => row.code },
  { header: "Nom", value: (row) => row.name },
  { header: "Unité", value: (row) => row.unit_label },
  { header: "Stock", value: (row) => row.total_stock ?? "0" },
  { header: "Fournisseur", value: (row) => row.supplier ?? "" },
  { header: "Stock bas", value: (row) => (row.low_stock ? "Oui" : "Non") },
]

function MetricCard({
  icon: Icon,
  label,
  value,
  destructive,
}: {
  icon: typeof AlertTriangle
  label: string
  value: number
  destructive?: boolean
}) {
  return (
    <Card className="rounded-lg shadow-none">
      <CardContent className="flex items-center gap-3 p-4">
        <div
          className={
            destructive
              ? "flex size-9 items-center justify-center rounded-lg bg-destructive/10 text-destructive"
              : "flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary"
          }
        >
          <Icon className="size-4" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold">{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function FilterSelect({
  label,
  value,
  onValueChange,
  options,
}: {
  label: string
  value: string
  onValueChange: (value: string) => void
  options: Array<[string, string]>
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger size="sm" className="w-44">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map(([optionValue, optionLabel]) => (
            <SelectItem key={optionValue} value={optionValue}>
              {optionLabel}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

function ReagentDetailSheet({
  reagent,
  canManage,
  canRecord,
  onOpenChange,
  onEdit,
  onReceive,
  onMovement,
  onDelete,
  onRestore,
}: {
  reagent: ReagentPublic | null
  canManage: boolean
  canRecord: boolean
  onOpenChange: (open: boolean) => void
  onEdit: (reagent: ReagentPublic) => void
  onReceive: (reagent: ReagentPublic) => void
  onMovement: (lot: ReagentLotPublic) => void
  onDelete: (reagent: ReagentPublic) => void
  onRestore: (reagent: ReagentPublic) => void
}) {
  const lotsQuery = useQuery({
    queryKey: [...QUERY_KEY, "lots", reagent?.id],
    queryFn: () =>
      ReagentsService.readReagentLots({
        reagentId: reagent?.id,
        limit: 100,
      }),
    enabled: !!reagent,
  })
  const movementsQuery = useQuery({
    queryKey: [...QUERY_KEY, "movements", reagent?.id],
    queryFn: () =>
      ReagentsService.readReagentMovements({
        reagentId: reagent?.id,
        limit: 25,
      }),
    enabled: !!reagent,
  })

  return (
    <Sheet open={!!reagent} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-3xl">
        {reagent && (
          <>
            <SheetHeader>
              <SheetTitle>{reagent.name}</SheetTitle>
              <SheetDescription>
                {reagent.code} ·{" "}
                {quantity(reagent.total_stock, reagent.unit_label)}
              </SheetDescription>
            </SheetHeader>
            <div className="flex flex-col gap-4 px-6 pb-6">
              <div className="flex flex-wrap gap-2">
                {canManage && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEdit(reagent)}
                    >
                      Modifier
                    </Button>
                    {reagent.is_deleted ? (
                      <Button size="sm" onClick={() => onRestore(reagent)}>
                        <ArchiveRestore className="size-4" />
                        Restaurer
                      </Button>
                    ) : (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => onDelete(reagent)}
                      >
                        <Trash2 className="size-4" />
                        Supprimer
                      </Button>
                    )}
                  </>
                )}
                {canRecord && !reagent.is_deleted && (
                  <Button size="sm" onClick={() => onReceive(reagent)}>
                    <PackagePlus className="size-4" />
                    Réceptionner un lot
                  </Button>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <Info
                  label="Stock minimum"
                  value={reagent.minimum_stock_level ?? "—"}
                />
                <Info
                  label="Lots actifs"
                  value={String(reagent.active_lot_count ?? 0)}
                />
                <Info
                  label="Alerte expiration"
                  value={
                    reagent.expiry_warning_days_override
                      ? `${reagent.expiry_warning_days_override} jours`
                      : "Défaut labo"
                  }
                />
              </div>

              <Card className="rounded-lg shadow-none">
                <CardHeader>
                  <CardTitle className="text-sm">Lots</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(lotsQuery.data?.data ?? []).map((lot) => (
                    <div
                      key={lot.id}
                      className="flex flex-col gap-2 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{lot.lot_number}</span>
                          <Badge variant={expiryTone(lot.expiry_status)}>
                            {expiryLabel(lot.expiry_status)}
                          </Badge>
                          <Badge variant="outline">{lot.status}</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Expire le {lot.expiry_date} · Stock{" "}
                          {quantity(lot.current_quantity, lot.unit_label)}
                        </p>
                      </div>
                      {canRecord && lot.status === "active" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onMovement(lot)}
                        >
                          Mouvement
                        </Button>
                      )}
                    </div>
                  ))}
                  {!lotsQuery.data?.data.length && (
                    <p className="text-sm text-muted-foreground">Aucun lot.</p>
                  )}
                </CardContent>
              </Card>

              <Card className="rounded-lg shadow-none">
                <CardHeader>
                  <CardTitle className="text-sm">Mouvements récents</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(movementsQuery.data?.data ?? []).map((movement) => (
                    <div
                      key={movement.id}
                      className="flex items-center justify-between gap-3 rounded-md border p-3"
                    >
                      <div>
                        <p className="font-medium">
                          {movementLabel(movement.movement_type)} · Lot{" "}
                          {movement.lot_number}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {movement.reason} ·{" "}
                          {formatDateTime(movement.performed_at)}
                        </p>
                      </div>
                      <span className="font-medium">
                        {quantity(movement.quantity, reagent.unit_label)}
                      </span>
                    </div>
                  ))}
                  {!movementsQuery.data?.data.length && (
                    <p className="text-sm text-muted-foreground">
                      Aucun mouvement enregistré.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  )
}

function ReagentDialog({
  reagent,
  onOpenChange,
}: {
  reagent: ReagentPublic | null | "new"
  onOpenChange: () => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isOpen = reagent !== null
  const isEdit = reagent !== "new" && reagent !== null
  const [form, setForm] = useState({
    code: "",
    name: "",
    unit_label: "",
    supplier: "",
    storage_location: "",
    storage_condition: "",
    minimum_stock_level: "",
    expiry_warning_days_override: "",
    notes: "",
  })

  useEffect(() => {
    if (reagent && reagent !== "new") {
      setForm({
        code: reagent.code,
        name: reagent.name,
        unit_label: reagent.unit_label,
        supplier: reagent.supplier ?? "",
        storage_location: reagent.storage_location ?? "",
        storage_condition: reagent.storage_condition ?? "",
        minimum_stock_level: reagent.minimum_stock_level ?? "",
        expiry_warning_days_override: reagent.expiry_warning_days_override
          ? String(reagent.expiry_warning_days_override)
          : "",
        notes: reagent.notes ?? "",
      })
    } else {
      setForm({
        code: "",
        name: "",
        unit_label: "",
        supplier: "",
        storage_location: "",
        storage_condition: "",
        minimum_stock_level: "",
        expiry_warning_days_override: "",
        notes: "",
      })
    }
  }, [reagent])

  const mutation = useMutation({
    mutationFn: () => {
      const requestBody = {
        ...form,
        supplier: form.supplier || null,
        storage_location: form.storage_location || null,
        storage_condition: form.storage_condition || null,
        notes: form.notes || null,
        minimum_stock_level: form.minimum_stock_level || null,
        expiry_warning_days_override: form.expiry_warning_days_override
          ? Number(form.expiry_warning_days_override)
          : null,
      }
      if (isEdit) {
        return ReagentsService.updateReagent({
          reagentId: reagent.id,
          requestBody,
        })
      }
      return ReagentsService.createReagent({ requestBody })
    },
    onSuccess: () => {
      showSuccessToast(isEdit ? "Réactif mis à jour" : "Réactif créé")
      onOpenChange()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onOpenChange()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le réactif" : "Ajouter un réactif"}
          </DialogTitle>
          <DialogDescription>
            Les champs marqués d’un astérisque sont obligatoires.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field
            label="Code *"
            value={form.code}
            onChange={(code) => setForm({ ...form, code })}
          />
          <Field
            label="Nom *"
            value={form.name}
            onChange={(name) => setForm({ ...form, name })}
          />
          <Field
            label="Unité *"
            value={form.unit_label}
            onChange={(unit_label) => setForm({ ...form, unit_label })}
          />
          <Field
            label="Fournisseur"
            value={form.supplier}
            onChange={(supplier) => setForm({ ...form, supplier })}
          />
          <Field
            label="Emplacement"
            value={form.storage_location}
            onChange={(storage_location) =>
              setForm({ ...form, storage_location })
            }
          />
          <Field
            label="Conservation"
            value={form.storage_condition}
            onChange={(storage_condition) =>
              setForm({ ...form, storage_condition })
            }
          />
          <Field
            label="Stock minimum"
            type="number"
            value={form.minimum_stock_level}
            onChange={(minimum_stock_level) =>
              setForm({ ...form, minimum_stock_level })
            }
          />
          <Field
            label="Alerte expiration (jours)"
            type="number"
            value={form.expiry_warning_days_override}
            onChange={(expiry_warning_days_override) =>
              setForm({ ...form, expiry_warning_days_override })
            }
          />
          <div className="sm:col-span-2">
            <Label>Notes</Label>
            <Textarea
              value={form.notes}
              onChange={(event) =>
                setForm({ ...form, notes: event.currentTarget.value })
              }
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onOpenChange}>
            Annuler
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              !form.code || !form.name || !form.unit_label || mutation.isPending
            }
          >
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ReceiveLotDialog({
  reagent,
  onOpenChange,
}: {
  reagent: ReagentPublic | null
  onOpenChange: () => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [form, setForm] = useState({
    lot_number: "",
    expiry_date: "",
    received_date: today,
    initial_quantity: "",
    unit_cost: "",
    supplier_name: "",
    location: "",
    notes: "",
  })

  useEffect(() => {
    if (reagent) {
      setForm({
        lot_number: "",
        expiry_date: "",
        received_date: today,
        initial_quantity: "",
        unit_cost: "",
        supplier_name: reagent.supplier ?? "",
        location: reagent.storage_location ?? "",
        notes: "",
      })
    }
  }, [reagent])

  const mutation = useMutation({
    mutationFn: () =>
      ReagentsService.createReagentLot({
        requestBody: {
          reagent_id: reagent?.id ?? "",
          lot_number: form.lot_number,
          expiry_date: form.expiry_date,
          received_date: form.received_date,
          initial_quantity: form.initial_quantity,
          unit_cost: form.unit_cost || null,
          supplier_name: form.supplier_name || null,
          location: form.location || null,
          notes: form.notes || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Lot réceptionné")
      onOpenChange()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  return (
    <Dialog open={!!reagent} onOpenChange={(open) => !open && onOpenChange()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Réceptionner un lot</DialogTitle>
          <DialogDescription>{reagent?.name}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field
            label="N° de lot *"
            value={form.lot_number}
            onChange={(lot_number) => setForm({ ...form, lot_number })}
          />
          <Field
            label="Quantité *"
            type="number"
            value={form.initial_quantity}
            onChange={(initial_quantity) =>
              setForm({ ...form, initial_quantity })
            }
          />
          <Field
            label="Date d'expiration *"
            type="date"
            value={form.expiry_date}
            onChange={(expiry_date) => setForm({ ...form, expiry_date })}
          />
          <Field
            label="Date de réception *"
            type="date"
            value={form.received_date}
            onChange={(received_date) => setForm({ ...form, received_date })}
          />
          <Field
            label="Coût unitaire"
            type="number"
            value={form.unit_cost}
            onChange={(unit_cost) => setForm({ ...form, unit_cost })}
          />
          <Field
            label="Fournisseur"
            value={form.supplier_name}
            onChange={(supplier_name) => setForm({ ...form, supplier_name })}
          />
          <Field
            label="Emplacement"
            value={form.location}
            onChange={(location) => setForm({ ...form, location })}
          />
          <div>
            <Label>Notes</Label>
            <Textarea
              value={form.notes}
              onChange={(event) =>
                setForm({ ...form, notes: event.currentTarget.value })
              }
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onOpenChange}>
            Annuler
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              !form.lot_number ||
              !form.expiry_date ||
              !form.received_date ||
              !form.initial_quantity ||
              mutation.isPending
            }
          >
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function MovementDialog({
  lot,
  onOpenChange,
}: {
  lot: ReagentLotPublic | null
  onOpenChange: () => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [movementType, setMovementType] = useState<ReagentMovementType>("used")
  const [quantityInput, setQuantityInput] = useState("")
  const [reason, setReason] = useState("")
  const [notes, setNotes] = useState("")

  useEffect(() => {
    if (lot) {
      setMovementType("used")
      setQuantityInput("")
      setReason("")
      setNotes("")
    }
  }, [lot])

  const mutation = useMutation({
    mutationFn: () =>
      ReagentsService.createReagentMovement({
        requestBody: {
          lot_id: lot?.id ?? "",
          movement_type: movementType,
          quantity:
            movementType === "disposed"
              ? (lot?.current_quantity ?? quantityInput)
              : quantityInput,
          reason: reason || movementLabel(movementType),
          notes: notes || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Mouvement enregistré")
      onOpenChange()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  return (
    <Dialog open={!!lot} onOpenChange={(open) => !open && onOpenChange()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enregistrer un mouvement</DialogTitle>
          <DialogDescription>
            Lot {lot?.lot_number} · Stock{" "}
            {quantity(lot?.current_quantity, lot?.unit_label)}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3">
          <div className="grid gap-1.5">
            <Label>Type</Label>
            <Select
              value={movementType}
              onValueChange={(value) =>
                setMovementType(value as ReagentMovementType)
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="used">Utilisation</SelectItem>
                <SelectItem value="adjusted">Ajustement positif</SelectItem>
                <SelectItem value="disposed">Élimination</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Field
            label="Quantité"
            type="number"
            value={
              movementType === "disposed"
                ? (lot?.current_quantity ?? "")
                : quantityInput
            }
            disabled={movementType === "disposed"}
            onChange={setQuantityInput}
          />
          <Field label="Motif *" value={reason} onChange={setReason} />
          <div>
            <Label>Notes</Label>
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.currentTarget.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onOpenChange}>
            Annuler
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              mutation.isPending ||
              !reason ||
              (movementType !== "disposed" && numberValue(quantityInput) <= 0)
            }
          >
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function SettingsDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const settingsQuery = useQuery({
    queryKey: [...QUERY_KEY, "settings"],
    queryFn: () => ReagentsService.readReagentSettings(),
    enabled: open,
  })
  const [days, setDays] = useState("30")
  const [expiryAlerts, setExpiryAlerts] = useState("true")
  const [lowStockAlerts, setLowStockAlerts] = useState("true")

  useEffect(() => {
    if (settingsQuery.data) {
      setDays(String(settingsQuery.data.default_expiry_warning_days ?? 30))
      setExpiryAlerts(String(settingsQuery.data.expiry_alerts_enabled ?? true))
      setLowStockAlerts(
        String(settingsQuery.data.low_stock_alerts_enabled ?? true),
      )
    }
  }, [settingsQuery.data])

  const mutation = useMutation({
    mutationFn: () =>
      ReagentsService.updateReagentSettings({
        requestBody: {
          default_expiry_warning_days: Number(days),
          expiry_alerts_enabled: expiryAlerts === "true",
          low_stock_alerts_enabled: lowStockAlerts === "true",
        },
      }),
    onSuccess: () => {
      showSuccessToast("Réglages enregistrés")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Réglages des réactifs</DialogTitle>
          <DialogDescription>
            Configurer les alertes opérationnelles.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3">
          <Field
            label="Alerte expiration par défaut (jours)"
            type="number"
            value={days}
            onChange={setDays}
          />
          <FilterSelect
            label="Alertes expiration"
            value={expiryAlerts}
            onValueChange={setExpiryAlerts}
            options={[
              ["true", "Activées"],
              ["false", "Désactivées"],
            ]}
          />
          <FilterSelect
            label="Alertes stock bas"
            value={lowStockAlerts}
            onValueChange={setLowStockAlerts}
            options={[
              ["true", "Activées"],
              ["false", "Désactivées"],
            ]}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={numberValue(days) <= 0 || mutation.isPending}
          >
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  disabled,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  disabled?: boolean
}) {
  return (
    <div className="grid gap-1.5">
      <Label>{label}</Label>
      <Input
        type={type}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.value)}
      />
    </div>
  )
}
