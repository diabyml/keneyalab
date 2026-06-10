import { useMutation, useQueryClient } from "@tanstack/react-query"

import { UnitsService } from "@/client"
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

interface DeleteUniteDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeleteUniteDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeleteUniteDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteUnit = async (id: string) => {
    await UnitsService.deleteUnit({ id })
  }

  const mutation = useMutation({
    mutationFn: deleteUnit,
    onSuccess: () => {
      showSuccessToast(`L'unité « ${name} » a été supprimée`)
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
          <DialogTitle>Supprimer l'unité « {name} » ?</DialogTitle>
          <DialogDescription>
            Cette unité sera <strong>désactivée</strong>. Elle ne sera plus
            disponible pour les nouveaux analytes mais restera sur les
            enregistrements existants.
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
