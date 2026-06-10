import { useMutation, useQueryClient } from "@tanstack/react-query"

import { DoctorsService } from "@/client"
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

interface DeleteDoctorDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeleteDoctorDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeleteDoctorDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const mutation = useMutation({
    mutationFn: () => DoctorsService.deleteDoctor({ id }),
    onSuccess: () => {
      showSuccessToast(`Le médecin « ${name} » a été supprimé`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["doctors"] })
      queryClient.invalidateQueries({ queryKey: ["doctor", id] })
    },
  })

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer ce médecin ?</AlertDialogTitle>
          <AlertDialogDescription>
            Le médecin sera masqué des listes actives. Il pourra être restauré
            depuis le filtre des médecins supprimés.
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
