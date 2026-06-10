import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { InsuranceProviderPublic } from "@/client"
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

const formSchema = z.object({ name: z.string().min(1, "Le nom est requis") })
type FormData = z.infer<typeof formSchema>

interface Props {
  open: boolean
  onOpenChange: (o: boolean) => void
  item: InsuranceProviderPublic | null
}

export function AssureurDialog({ open, onOpenChange, item }: Props) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = item !== null
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { name: "" },
  })
  useEffect(() => {
    if (open) form.reset({ name: item?.name ?? "" })
  }, [open, item, form])

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (isEdit)
        await InsuranceProvidersService.updateInsuranceProvider({
          id: item!.id,
          requestBody: { name: data.name },
        })
      else
        await InsuranceProvidersService.createInsuranceProvider({
          requestBody: { name: data.name },
        })
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit ? "Assureur mis à jour" : "Assureur créé avec succès",
      )
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      qc.invalidateQueries({ queryKey: ["insurance-providers"] }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier l'assureur" : "Ajouter un assureur"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modifiez le nom de l'assureur."
              : "Ajoutez un nouvel assureur (CNAS, AXA, etc.)."}
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
                      <Input placeholder="ex. CNAS" type="text" {...field} />
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
