import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, ShieldCheck, X } from "lucide-react"
import { useState } from "react"

import type { RolePublic, UserPublic, UserRolePublic } from "@/client"
import { RbacService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface AssignmentDialogProps {
  user: UserPublic | null
  roles: RolePublic[]
  open: boolean
  onOpenChange: (open: boolean) => void
}

function AssignmentDialog({
  user,
  roles,
  open,
  onOpenChange,
}: AssignmentDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selectedRole, setSelectedRole] = useState("")

  // Fetch current assignments
  const {
    data: assignments = [],
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["userRoles", user?.id],
    queryFn: () => RbacService.listUserRoles({ userId: user!.id }),
    enabled: open && !!user,
  })

  const assignedRoleIds = assignments.map((ur: UserRolePublic) => ur.role_id)
  const availableRoles = roles.filter(
    (r) => !assignedRoleIds.includes(r.id) && !r.is_deleted,
  )

  // Assign
  const assignMutation = useMutation({
    mutationFn: (roleId: string) =>
      RbacService.assignRoleToUser({
        userId: user!.id,
        requestBody: { role_id: roleId },
      }),
    onSuccess: () => {
      showSuccessToast("Rôle assigné avec succès")
      setSelectedRole("")
      refetch()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  // Revoke
  const revokeMutation = useMutation({
    mutationFn: (roleId: string) =>
      RbacService.removeRoleFromUser({
        userId: user!.id,
        roleId,
      }),
    onSuccess: () => {
      showSuccessToast("Rôle révoqué avec succès")
      refetch()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  if (!user) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Gérer les rôles</DialogTitle>
          <DialogDescription>
            Assigner ou révoquer des rôles pour cet utilisateur.
          </DialogDescription>
        </DialogHeader>

        {/* User summary */}
        <div className="flex items-center gap-3 rounded-lg border bg-muted/30 p-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-medium">
            {user.full_name
              ?.split(" ")
              .map((n) => n[0])
              .join("")
              .slice(0, 2)
              .toUpperCase() || user.email[0]?.toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="truncate font-medium">
              {user.full_name || user.email}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {user.email}
            </p>
          </div>
        </div>

        {/* Assign a role */}
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Assigner un rôle</p>
          <div className="flex gap-2">
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger className="flex-1">
                <SelectValue
                  placeholder={
                    availableRoles.length
                      ? "Sélectionner un rôle"
                      : "Tous les rôles sont assignés"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {availableRoles.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <LoadingButton
              onClick={() => {
                if (selectedRole) assignMutation.mutate(selectedRole)
              }}
              disabled={!selectedRole || !availableRoles.length}
              loading={assignMutation.isPending}
              className="shrink-0"
            >
              <Plus className="size-4" />
              Assigner
            </LoadingButton>
          </div>
        </div>

        <Separator />

        {/* Current roles */}
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">
            Rôles actuels ({assignments.length})
          </p>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </div>
          ) : assignments.length === 0 ? (
            <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              Aucun rôle assigné.
            </div>
          ) : (
            <ScrollArea className="max-h-64">
              <div className="flex flex-col gap-2">
                {assignments.map((ur: UserRolePublic) => {
                  const role = ur.role ?? roles.find((r) => r.id === ur.role_id)
                  if (!role) return null
                  return (
                    <div
                      key={ur.id}
                      className="flex items-center justify-between gap-3 rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex size-8 items-center justify-center rounded-md bg-primary/10 text-primary">
                          <ShieldCheck className="size-4" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{role.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {role.description || "Aucune description"}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-8 text-muted-foreground hover:text-destructive"
                        onClick={() => revokeMutation.mutate(role.id)}
                        disabled={revokeMutation.isPending}
                      >
                        <X className="size-4" />
                        <span className="sr-only">Révoquer le rôle</span>
                      </Button>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default AssignmentDialog
