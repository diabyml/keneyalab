import { useMutation, useQueryClient } from "@tanstack/react-query"

import { TitlesService } from "@/client"
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

interface DeleteTitreDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeleteTitreDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeleteTitreDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteTitle = async (id: string) => {
    await TitlesService.deleteTitle({ id })
  }

  const mutation = useMutation({
    mutationFn: deleteTitle,
    onSuccess: () => {
      showSuccessToast(`Le titre « ${name} » a été supprimé`)
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
          <DialogTitle>Supprimer le titre « {name} » ?</DialogTitle>
          <DialogDescription>
            Ce titre sera <strong>désactivé</strong>. Il ne sera plus disponible
            pour les nouveaux docteurs mais restera sur les enregistrements
            existants.
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
            onClick={() => mutation.mutate(id)}
          >
            Supprimer
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
