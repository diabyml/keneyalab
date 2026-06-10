import { useMutation, useQueryClient } from "@tanstack/react-query"

import { CategoriesService } from "@/client"
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

interface DeleteCategoryDialogProps {
  id: string
  name: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeleteCategoryDialog({
  id,
  name,
  open,
  onOpenChange,
}: DeleteCategoryDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (id: string) => CategoriesService.deleteCategory({ id }),
    onSuccess: () => {
      showSuccessToast(`La catégorie « ${name} » a été supprimée`)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Supprimer la catégorie « {name} » ?</DialogTitle>
          <DialogDescription>
            Cette catégorie sera <strong>désactivée</strong>. Elle ne sera plus
            proposée pour organiser le catalogue.
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
