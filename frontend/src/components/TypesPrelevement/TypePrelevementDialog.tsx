import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { SpecimenTypePublic } from "@/client"
import { SpecimenTypesService } from "@/client"
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
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  name: z.string().min(1, "Le nom est requis"),
  description: z.string().optional(),
  color: z.string().optional(),
})
type FormData = z.infer<typeof formSchema>

interface Props {
  open: boolean
  onOpenChange: (o: boolean) => void
  item: SpecimenTypePublic | null
}

export function TypePrelevementDialog({ open, onOpenChange, item }: Props) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = item !== null
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { name: "", description: "", color: "#3b82f6" },
  })
  useEffect(() => {
    if (open)
      form.reset({
        name: item?.name ?? "",
        description: item?.description ?? "",
        color: item?.color ?? "#3b82f6",
      })
  }, [open, item, form])

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      const body = {
        name: data.name,
        description: data.description || null,
        color: data.color || null,
      }
      if (isEdit)
        await SpecimenTypesService.updateSpecimenType({
          id: item!.id,
          requestBody: body,
        })
      else await SpecimenTypesService.createSpecimenType({ requestBody: body })
    },
    onSuccess: () => {
      showSuccessToast(isEdit ? "Type mis à jour" : "Type créé avec succès")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => qc.invalidateQueries({ queryKey: ["specimen-types"] }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le type" : "Ajouter un type de prélèvement"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modifiez les informations du type."
              : "Ajoutez un nouveau type de prélèvement."}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))}>
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
                        placeholder="ex. Sang veineux"
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
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Description du type de prélèvement"
                        rows={2}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="color"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Couleur</FormLabel>
                    <FormControl>
                      <div className="flex items-center gap-3">
                        <input
                          type="color"
                          value={field.value || "#3b82f6"}
                          onChange={(e) => field.onChange(e.target.value)}
                          className="size-9 cursor-pointer rounded border p-0.5"
                        />
                        <Input
                          placeholder="#3b82f6"
                          type="text"
                          {...field}
                          className="w-28 font-mono text-xs"
                        />
                      </div>
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
