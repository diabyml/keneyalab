import { useSuspenseQuery } from "@tanstack/react-query"
import { Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { Suspense, useMemo, useState } from "react"
import { PaymentMethodsService } from "@/client"
import { SimpleTable } from "@/components/Common/SimpleTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyDescription,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { columns } from "./columns"
import { MethodePaiementDialog } from "./MethodePaiementDialog"

type StatusFilter = "active" | "deleted" | "all"
function getQueryOptions(sf: StatusFilter) {
  return {
    queryKey: ["payment-methods", { includeDeleted: sf }],
    queryFn: () =>
      PaymentMethodsService.readPaymentMethods({
        limit: 200,
        includeDeleted: sf !== "active" || undefined,
      }),
  }
}
function Skel() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

export function MethodesPaiementView() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("active")
  const [showFilters, setShowFilters] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const ac = statusFilter !== "active" ? 1 : 0
  const ha = ac > 0 || search.trim() !== ""

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher une méthode…"
            className="pl-9"
            aria-label="Rechercher"
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
            {ac > 0 && (
              <Badge
                variant="secondary"
                className="ml-1 bg-primary text-primary-foreground"
              >
                {ac}
              </Badge>
            )}
          </Button>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus />
            Ajouter
          </Button>
        </div>
      </div>
      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="filter-status-pm"
                className="text-xs font-medium text-muted-foreground"
              >
                Statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as StatusFilter)}
              >
                <SelectTrigger id="filter-status-pm" size="sm" className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Actives</SelectItem>
                  <SelectItem value="deleted">Supprimées</SelectItem>
                  <SelectItem value="all">Toutes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearch("")
                setStatusFilter("active")
              }}
              disabled={!ha}
              className="text-muted-foreground"
            >
              <X className="size-4" />
              Réinitialiser
            </Button>
          </div>
        </div>
      )}
      <Suspense fallback={<Skel />}>
        <TableWithMeta
          search={search}
          statusFilter={statusFilter}
          hasActive={ha}
        />
      </Suspense>
      <MethodePaiementDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        item={null}
      />
    </div>
  )
}

function TableWithMeta({
  search,
  statusFilter,
  hasActive,
}: {
  search: string
  statusFilter: StatusFilter
  hasActive: boolean
}) {
  const { data } = useSuspenseQuery(getQueryOptions(statusFilter))
  const filtered = useMemo(() => {
    let rows = data.data
    if (statusFilter === "active") rows = rows.filter((r) => !r.is_deleted)
    else if (statusFilter === "deleted") rows = rows.filter((r) => r.is_deleted)
    const q = search.toLowerCase().trim()
    if (q) rows = rows.filter((r) => r.name.toLowerCase().includes(q))
    return rows
  }, [data, search, statusFilter])
  if (filtered.length === 0)
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <Search />
        </EmptyMedia>
        <EmptyTitle>Aucune méthode trouvée</EmptyTitle>
        <EmptyDescription>
          Essayez d'ajuster votre recherche ou vos filtres.
        </EmptyDescription>
      </Empty>
    )
  return (
    <>
      <div className="flex items-center px-0.5 text-sm text-muted-foreground">
        <span>
          <span className="font-medium text-foreground">{filtered.length}</span>{" "}
          méthode{filtered.length !== 1 && "s"}
          {hasActive && (
            <span>
              {" "}
              · filtrée{filtered.length !== 1 && "s"} de {data.data.length}
            </span>
          )}
        </span>
      </div>
      <SimpleTable columns={columns} data={filtered} />
    </>
  )
}
