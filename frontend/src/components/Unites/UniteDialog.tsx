import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { UnitPublic } from "@/client"
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  name: z.string().min(1, "Le nom est requis"),
})

type FormData = z.infer<typeof formSchema>

interface UniteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  unit: UnitPublic | null
}

export function UniteDialog({ open, onOpenChange, unit }: UniteDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = unit !== null

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
    },
  })

  useEffect(() => {
    if (open) {
      form.reset({
        name: unit?.name ?? "",
      })
    }
  }, [open, unit, form])

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (isEdit) {
        await UnitsService.updateUnit({
          id: unit!.id,
          requestBody: { name: data.name },
        })
      } else {
        await UnitsService.createUnit({
          requestBody: { name: data.name },
        })
      }
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit ? "Unité mise à jour avec succès" : "Unité créée avec succès",
      )
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["units"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier l'unité" : "Ajouter une unité"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modifiez le nom de l'unité de mesure."
              : "Ajoutez une nouvelle unité de mesure (mg/dL, g/L, etc.)."}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Nom <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="ex. mg/dL" type="text" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Annuler
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                {isEdit ? "Enregistrer" : "Créer"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
