import { useMutation, useQueryClient } from "@tanstack/react-query"

import { PatientsService } from "@/client"
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

interface DeletePatientDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeletePatientDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeletePatientDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const mutation = useMutation({
    mutationFn: () => PatientsService.deletePatient({ id }),
    onSuccess: () => {
      showSuccessToast(`Le patient « ${name} » a été supprimé`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["patients"] })
      queryClient.invalidateQueries({ queryKey: ["patient", id] })
    },
  })

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer ce patient ?</AlertDialogTitle>
          <AlertDialogDescription>
            Le patient sera masqué des listes actives. Il pourra être restauré
            depuis le filtre des patients supprimés.
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
