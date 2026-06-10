import { useSuspenseQuery } from "@tanstack/react-query"
import type { ColumnDef } from "@tanstack/react-table"
import { Search } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import { RbacService } from "@/client"
import type { PermissionPublic } from "@/client/types.gen"
import { SimpleTable } from "@/components/Common/SimpleTable"
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

import { ActionBadge } from "../Roles/PermissionBadge"

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function getPermissionsQueryOptions() {
  return {
    queryKey: ["permissions"],
    queryFn: () => RbacService.listPermissions({ limit: 500 }),
  }
}

// ─── Column definitions ────────────────────────────────────────

const columns: ColumnDef<PermissionPublic>[] = [
  {
    accessorKey: "resource",
    header: "Ressource",
    cell: ({ getValue }) => (
      <span className="font-mono font-medium">{getValue<string>()}</span>
    ),
  },
  {
    accessorKey: "action",
    header: "Action",
    cell: ({ getValue }) => <ActionBadge action={getValue<string>()} />,
  },
  {
    accessorKey: "description",
    header: () => <span className="hidden md:table-cell">Description</span>,
    cell: ({ getValue }) => {
      const val = getValue<string | null>()
      return (
        <span className="hidden max-w-xs truncate text-muted-foreground md:table-cell">
          {val || "—"}
        </span>
      )
    },
  },
  {
    accessorKey: "created_at",
    header: () => <span className="hidden lg:table-cell">Créé le</span>,
    cell: ({ getValue }) => {
      const val = getValue<string>()
      return (
        <span className="hidden text-muted-foreground lg:table-cell">
          {val ? formatDate(val) : "—"}
        </span>
      )
    },
  },
]

// ─── Inner data component (Suspense boundary) ──────────────────

function PermissionsTable({
  search,
  actionFilter,
}: {
  search: string
  actionFilter: string
}) {
  const { data: permsData } = useSuspenseQuery(getPermissionsQueryOptions())
  const permissions = permsData.data

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    return permissions.filter((p) => {
      const matchesQuery =
        !q ||
        p.resource.toLowerCase().includes(q) ||
        p.action.toLowerCase().includes(q) ||
        (p.description ?? "").toLowerCase().includes(q)
      const matchesAction = actionFilter === "all" || p.action === actionFilter
      return matchesQuery && matchesAction
    })
  }, [permissions, search, actionFilter])

  if (filtered.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <Search />
        </EmptyMedia>
        <EmptyTitle>Aucune permission trouvée</EmptyTitle>
        <EmptyDescription>Essayez d'ajuster vos filtres.</EmptyDescription>
      </Empty>
    )
  }

  return (
    <>
      <SimpleTable columns={columns} data={filtered} />

      <p className="text-xs text-muted-foreground">
        {filtered.length} permission{filtered.length > 1 ? "s" : ""} affichée
        {filtered.length > 1 ? "s" : ""} sur {permissions.length}
      </p>
    </>
  )
}

// ─── Outer view component ──────────────────────────────────────

function PermissionsView() {
  const [search, setSearch] = useState("")
  const [actionFilter, setActionFilter] = useState("all")

  return (
    <div className="flex flex-col gap-6">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Rechercher une permission…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toutes les actions</SelectItem>
            {[
              "create",
              "view",
              "edit",
              "delete",
              "manage",
              "collect",
              "verify",
              "release",
              "enter",
              "cancel",
              "reject",
              "void",
              "refund",
              "pay",
              "acknowledge",
            ].map((a) => (
              <SelectItem key={a} value={a} className="capitalize">
                {a}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table with Suspense */}
      <Suspense
        fallback={
          <div className="flex flex-col gap-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="h-10 w-full animate-pulse rounded-md bg-muted"
              />
            ))}
          </div>
        }
      >
        <PermissionsTable search={search} actionFilter={actionFilter} />
      </Suspense>
    </div>
  )
}

export default PermissionsView
