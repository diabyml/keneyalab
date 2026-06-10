import { useMutation, useQueryClient } from "@tanstack/react-query"

import { RbacService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteRoleDialogProps {
  roleId: string
  roleName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function DeleteRoleDialog({
  roleId,
  roleName,
  open,
  onOpenChange,
}: DeleteRoleDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteRole = async (id: string) => {
    await RbacService.deleteRole({ roleId: id })
  }

  const mutation = useMutation({
    mutationFn: deleteRole,
    onSuccess: () => {
      showSuccessToast(`Le rôle « ${roleName} » a été supprimé`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Supprimer le rôle « {roleName} » ?</DialogTitle>
          <DialogDescription>
            Ce rôle sera <strong>désactivé</strong> et retiré de tous les
            utilisateurs auxquels il est assigné. Cette action peut être annulée
            en restaurant le rôle depuis la base de données.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="mt-4">
          <DialogClose asChild>
            <Button variant="outline" disabled={mutation.isPending}>
              Annuler
            </Button>
          </DialogClose>
          <LoadingButton
            variant="destructive"
            type="submit"
            loading={mutation.isPending}
            onClick={() => mutation.mutate(roleId)}
          >
            Supprimer
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteRoleDialog
