import { useQueries, useQuery, useSuspenseQuery } from "@tanstack/react-query"
import {
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  ShieldCheck,
  Star,
  Trash2,
} from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import type { PermissionPublic, RoleDetail, RolePublic } from "@/client"
import { RbacService } from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Empty,
  EmptyDescription,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"

import DeleteRoleDialog from "./DeleteRoleDialog"
import { PermissionPill } from "./PermissionBadge"
import RoleDialog from "./RoleDialog"

// ─── Query options ─────────────────────────────────────────────

function getRolesQueryOptions() {
  return {
    queryKey: ["roles"],
    queryFn: () => RbacService.listRoles({ limit: 200 }),
  }
}

function getPermissionsQueryOptions() {
  return {
    queryKey: ["permissions"],
    queryFn: () => RbacService.listPermissions({ limit: 500 }),
  }
}

// ─── Relative time helper ─────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const abs = Math.abs(diff)
  const days = Math.floor(abs / 86_400_000)
  if (days < 1) return "aujourd'hui"
  if (days < 30) return `il y a ${days} j`
  const months = Math.floor(days / 30)
  if (months < 12) return `il y a ${months} mois`
  return `il y a ${Math.floor(months / 12)} an(s)`
}

// ─── Skeleton ──────────────────────────────────────────────────

function RolesSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-48 rounded-xl" />
      ))}
    </div>
  )
}

// ─── Role card ─────────────────────────────────────────────────

function RoleCard({
  role,
  permissions,
  onEdit,
  onDelete,
}: {
  role: RolePublic
  permissions: PermissionPublic[]
  onEdit: (detail: RoleDetail) => void
  onDelete: (role: RolePublic) => void
}) {
  const MAX_PILLS = 5
  const overflow = permissions.length - MAX_PILLS

  return (
    <Card className="group flex flex-col hover:shadow-sm hover:border-primary/20">
      <CardContent className="flex flex-1 flex-col gap-3 p-4">
        {/* Header row */}
        <div className="flex items-start gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ShieldCheck className="size-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-semibold">
                {role.name}
              </span>
              {role.is_default && (
                <span className="inline-flex shrink-0 items-center gap-0.5 rounded-full bg-chart-3/10 px-1.5 py-0 text-[10px] font-medium text-chart-3">
                  <Star className="size-2.5" />
                  Par défaut
                </span>
              )}
            </div>
            <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
              {role.description || "Aucune description"}
            </p>
          </div>

          {/* Actions dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-xs"
                className="shrink-0 opacity-0 group-hover:opacity-100"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onEdit({ ...role, permissions })}
              >
                <Pencil />
                Modifier
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onClick={() => onDelete(role)}
              >
                <Trash2 />
                Supprimer
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Permission pills */}
        <div className="flex flex-wrap gap-1">
          {permissions.length === 0 && (
            <span className="text-xs text-muted-foreground">
              Aucune permission
            </span>
          )}
          {permissions.slice(0, MAX_PILLS).map((p) => (
            <PermissionPill
              key={p.id}
              resource={p.resource}
              action={p.action}
            />
          ))}
          {overflow > 0 && (
            <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              +{overflow} autres
            </span>
          )}
        </div>

        {/* Footer */}
        <div className="mt-auto flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
          <span>{permissions.length} permission(s)</span>
          <span>
            Mis à jour {role.updated_at ? relativeTime(role.updated_at) : "—"}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Inner data component (Suspense boundary) ──────────────────

function RolesGrid({
  onEdit,
  onDelete,
  search,
}: {
  onEdit: (detail: RoleDetail) => void
  onDelete: (role: RolePublic) => void
  search: string
}) {
  const { data: rolesData } = useSuspenseQuery(getRolesQueryOptions())
  const roles = rolesData.data

  // Fetch each role's detail to get permissions
  const detailResults = useQueries({
    queries: roles.map((r) => ({
      queryKey: ["role", r.id],
      queryFn: () => RbacService.getRole({ roleId: r.id }),
    })),
  })

  // Build a map of roleId → PermissionPublic[]
  const permMap = useMemo(() => {
    const map = new Map<string, PermissionPublic[]>()
    detailResults.forEach((result, i) => {
      if (result.data) {
        map.set(roles[i].id, result.data.permissions ?? [])
      }
    })
    return map
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detailResults, roles])

  // Filter by search
  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return roles
    return roles.filter((r) => r.name.toLowerCase().includes(q))
  }, [roles, search])

  if (filtered.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <Search />
        </EmptyMedia>
        <EmptyTitle>Aucun rôle trouvé</EmptyTitle>
        <EmptyDescription>Essayez d'ajuster votre recherche.</EmptyDescription>
      </Empty>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {filtered.map((role) => (
        <RoleCard
          key={role.id}
          role={role}
          permissions={permMap.get(role.id) ?? []}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

// ─── Outer view component ──────────────────────────────────────

function RolesView() {
  const [search, setSearch] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<RoleDetail | null>(null)
  const [toDelete, setToDelete] = useState<RolePublic | null>(null)

  // Fetch all permissions once for the dialog (no Suspense needed — loads async)
  const { data: permsData, isLoading: permsLoading } = useQuery(
    getPermissionsQueryOptions(),
  )
  const allPermissions = permsData?.data ?? []

  function openCreate() {
    setEditing(null)
    setDialogOpen(true)
  }

  function openEdit(detail: RoleDetail) {
    setEditing(detail)
    setDialogOpen(true)
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Rechercher un rôle…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button onClick={openCreate}>
          <Plus />
          Nouveau rôle
        </Button>
      </div>

      {/* Card grid */}
      <Suspense fallback={<RolesSkeleton />}>
        <RolesGrid onEdit={openEdit} onDelete={setToDelete} search={search} />
      </Suspense>

      {/* Create / Edit dialog */}
      <RoleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        role={editing}
        allPermissions={allPermissions}
        permissionsLoading={permsLoading}
      />

      {/* Delete confirmation */}
      {toDelete && (
        <DeleteRoleDialog
          roleId={toDelete.id}
          roleName={toDelete.name}
          open={!!toDelete}
          onOpenChange={(open) => {
            if (!open) setToDelete(null)
          }}
        />
      )}
    </div>
  )
}

export default RolesView
