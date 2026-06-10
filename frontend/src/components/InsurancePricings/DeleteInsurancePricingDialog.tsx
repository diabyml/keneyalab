import { useMutation, useQueryClient } from "@tanstack/react-query"

import { InsurancePricingsService } from "@/client"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteInsurancePricingDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onDeleted?: () => void
}

export function DeleteInsurancePricingDialog({
  id,
  name,
  open,
  onOpenChange,
  onDeleted,
}: DeleteInsurancePricingDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const mutation = useMutation({
    mutationFn: () => InsurancePricingsService.deleteInsurancePricing({ id }),
    onSuccess: () => {
      showSuccessToast(`Le tarif « ${name} » a été supprimé`)
      onOpenChange(false)
      onDeleted?.()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["insurance-pricings"] }),
  })

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer ce tarif assurance ?</AlertDialogTitle>
          <AlertDialogDescription>
            Cette suppression est définitive pour cette paire assureur/test.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>
            Annuler
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={mutation.isPending}
            onClick={(event) => {
              event.preventDefault()
              mutation.mutate()
            }}
          >
            Supprimer
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
