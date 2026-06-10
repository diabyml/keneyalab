import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { DoctorCommissionEntriesService } from "@/client"
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

const adjustmentSchema = z.object({
  amount: z
    .string()
    .trim()
    .min(1, "Le montant est requis")
    .refine((value) => {
      const amount = Number(value.replace(",", "."))
      return Number.isFinite(amount) && amount !== 0
    }, "Le montant doit être numérique et différent de zéro"),
  reason: z
    .string()
    .trim()
    .min(1, "Le motif est requis")
    .max(2000, "Le motif ne peut pas dépasser 2000 caractères"),
})

type AdjustmentFormData = z.infer<typeof adjustmentSchema>

interface AdjustmentDialogProps {
  entryId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AdjustmentDialog({
  entryId,
  open,
  onOpenChange,
}: AdjustmentDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<AdjustmentFormData>({
    resolver: zodResolver(adjustmentSchema),
    defaultValues: { amount: "", reason: "" },
  })

  useEffect(() => {
    if (open) form.reset({ amount: "", reason: "" })
  }, [form, open])

  const mutation = useMutation({
    mutationFn: (data: AdjustmentFormData) =>
      DoctorCommissionEntriesService.createAdjustment({
        id: entryId,
        requestBody: {
          amount: data.amount.replace(",", "."),
          reason: data.reason.trim(),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Ajustement de commission enregistré")
      queryClient.invalidateQueries({ queryKey: ["commission-entries"] })
      queryClient.invalidateQueries({
        queryKey: ["commission-entry", entryId],
      })
      queryClient.invalidateQueries({
        queryKey: ["doctor-commission-payments", "payable-lines"],
      })
      queryClient.invalidateQueries({
        queryKey: ["doctor-commission-payments"],
      })
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Ajouter un ajustement</DialogTitle>
          <DialogDescription>
            Saisissez un montant positif pour un complément ou négatif pour une
            retenue. Cette écriture ne pourra pas être modifiée.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Montant signé (XOF)</FormLabel>
                  <FormControl>
                    <Input
                      inputMode="decimal"
                      placeholder="-5 000 ou 5 000"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Motif</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={4}
                      placeholder="Décrivez la raison de l'ajustement…"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Annuler
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Enregistrer l'ajustement
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
