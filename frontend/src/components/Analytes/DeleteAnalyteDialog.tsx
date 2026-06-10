import { useMutation, useQueryClient } from "@tanstack/react-query"

import { AnalytesService } from "@/client"
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

interface DeleteAnalyteDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeleteAnalyteDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeleteAnalyteDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (id: string) => AnalytesService.deleteAnalyte({ id }),
    onSuccess: () => {
      showSuccessToast(`L'analyte « ${name} » a été supprimé`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["analytes"] })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Supprimer l'analyte « {name} » ?</DialogTitle>
          <DialogDescription>
            Cet analyte sera <strong>désactivé</strong>. Il ne sera plus proposé
            dans les nouveaux éléments du catalogue.
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
