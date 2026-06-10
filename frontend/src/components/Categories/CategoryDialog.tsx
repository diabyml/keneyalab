import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { CategoryPublic } from "@/client"
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
  sort_order: z
    .number({ message: "L'ordre doit être un nombre" })
    .int("L'ordre doit être un nombre entier")
    .min(0, "L'ordre doit être positif"),
})

type FormData = z.infer<typeof formSchema>

interface CategoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: CategoryPublic | null
  nextSortOrder: number
}

export function CategoryDialog({
  open,
  onOpenChange,
  category,
  nextSortOrder,
}: CategoryDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = category !== null

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      sort_order: nextSortOrder,
    },
  })

  useEffect(() => {
    if (open) {
      form.reset({
        name: category?.name ?? "",
        sort_order: category?.sort_order ?? nextSortOrder,
      })
    }
  }, [open, category, nextSortOrder, form])

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (isEdit) {
        await CategoriesService.updateCategory({
          id: category!.id,
          requestBody: data,
        })
      } else {
        await CategoriesService.createCategory({ requestBody: data })
      }
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit
          ? "Catégorie mise à jour avec succès"
          : "Catégorie créée avec succès",
      )
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
          <DialogTitle>
            {isEdit ? "Modifier la catégorie" : "Ajouter une catégorie"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modifiez le nom et l'ordre d'affichage de la catégorie."
              : "Ajoutez une catégorie pour regrouper les éléments du catalogue."}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
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
                      <Input
                        placeholder="ex. Biochimie"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="sort_order"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ordre d'affichage</FormLabel>
                    <FormControl>
                      <Input
                        min={0}
                        placeholder="0"
                        type="number"
                        value={field.value}
                        onBlur={field.onBlur}
                        name={field.name}
                        ref={field.ref}
                        onChange={(e) =>
                          field.onChange(e.currentTarget.valueAsNumber)
                        }
                      />
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
