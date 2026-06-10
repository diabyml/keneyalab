import type { ColumnDef } from "@tanstack/react-table"
import { EllipsisVertical, Settings2 } from "lucide-react"

import type { RolePublic, UserPublic, UserRolePublic } from "@/client"
import EditUser from "@/components/Admin/EditUser"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export interface UserTableData extends UserPublic {
  isCurrentUser: boolean
  assignments: UserRolePublic[]
  roles: RolePublic[]
}

export function buildColumns(
  onManageRoles: (user: UserTableData) => void,
  onRefresh: () => void,
): ColumnDef<UserTableData>[] {
  return [
    {
      accessorKey: "full_name",
      header: "Nom",
      cell: ({ row }) => {
        const user = row.original
        return (
          <div className="flex items-center gap-2">
            <span className="font-medium">{user.full_name || "N/D"}</span>
            {user.isCurrentUser && (
              <Badge variant="secondary" className="text-xs">
                Vous
              </Badge>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.email}</span>
      ),
    },
    {
      id: "roles",
      header: "Rôles",
      cell: ({ row }) => {
        const { assignments, roles } = row.original
        if (assignments.length === 0) {
          return (
            <span className="text-xs text-muted-foreground">Aucun rôle</span>
          )
        }
        return (
          <div className="flex flex-wrap gap-1">
            {assignments.map((ur) => {
              const role = ur.role ?? roles.find((r) => r.id === ur.role_id)
              if (!role) return null
              return (
                <Badge key={ur.id} variant="secondary" className="text-xs">
                  {role.name}
                </Badge>
              )
            })}
          </div>
        )
      },
    },
    {
      accessorKey: "is_active",
      header: "Statut",
      cell: ({ row }) => {
        const { is_active } = row.original
        return (
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "size-2 rounded-full",
                is_active ? "bg-primary" : "bg-muted-foreground/40",
              )}
            />
            <span className="text-sm text-muted-foreground">
              {is_active ? "Actif" : "Inactif"}
            </span>
          </div>
        )
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const user = row.original
        if (user.isCurrentUser) return null
        return (
          <div className="flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="size-8">
                  <EllipsisVertical className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <EditUser user={user} onSuccess={onRefresh} />
                <DropdownMenuItem
                  onSelect={(e) => e.preventDefault()}
                  onClick={() => onManageRoles(user)}
                >
                  <Settings2 />
                  Gérer les rôles
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )
      },
    },
  ]
}
