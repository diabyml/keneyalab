import { useMutation, useQueryClient } from "@tanstack/react-query"
import { AlertTriangle } from "lucide-react"

import { SpecimensService } from "@/client"
import { formatMoney } from "@/components/Orders/utils"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CollectAllSpecimensDialogProps {
  orderId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  pendingCount: number
  balanceDue?: string
}

export function CollectAllSpecimensDialog({
  orderId,
  open,
  onOpenChange,
  pendingCount,
  balanceDue = "0",
}: CollectAllSpecimensDialogProps) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const mutation = useMutation({
    mutationFn: () => SpecimensService.collectAllSpecimens({ orderId }),
    onSuccess: () => {
      showSuccessToast("Tous les prélèvements ont été enregistrés")
      onOpenChange(false)
      queryClient.invalidateQueries({ queryKey: ["order", orderId] })
      queryClient.invalidateQueries({
        queryKey: ["specimen-workspace", orderId],
      })
      queryClient.invalidateQueries({ queryKey: ["specimen-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const hasBalance = Number(balanceDue) > 0
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogMedia>
            <AlertTriangle className="size-7" />
          </AlertDialogMedia>
          <AlertDialogTitle>Tout marquer comme prélevé ?</AlertDialogTitle>
          <AlertDialogDescription>
            Les {pendingCount} prélèvement{pendingCount !== 1 && "s"} en attente
            seront enregistrés immédiatement avec l'heure actuelle.
          </AlertDialogDescription>
        </AlertDialogHeader>
        {hasBalance && (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
            Un solde de {formatMoney(balanceDue)} reste à payer. Le prélèvement
            reste autorisé.
          </div>
        )}
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
            {mutation.isPending ? "Enregistrement…" : "Confirmer"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
