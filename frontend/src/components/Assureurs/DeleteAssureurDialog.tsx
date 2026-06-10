import { useMutation, useQueryClient } from "@tanstack/react-query"
import { InsuranceProvidersService } from "@/client"
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

interface Props {
  id: string
  name: string
  open: boolean
  onOpenChange: (o: boolean) => void
}

export function DeleteAssureurDialog({ id, name, open, onOpenChange }: Props) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const mutation = useMutation({
    mutationFn: (id: string) =>
      InsuranceProvidersService.deleteInsuranceProvider({ id }),
    onSuccess: () => {
      showSuccessToast(`L'assureur « ${name} » a été supprimé`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => qc.invalidateQueries(),
  })
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Supprimer l'assureur « {name} » ?</DialogTitle>
          <DialogDescription>
            Cet assureur sera <strong>désactivé</strong>.
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
