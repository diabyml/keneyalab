import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { DoctorCommissionConfigPublic } from "@/client"
import { DoctorCommissionConfigsService, DoctorsService } from "@/client"
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
import { decimalToPercentString, percentToDecimalString } from "./utils"

const percentSchema = z
  .string()
  .trim()
  .min(1, "Le taux est requis")
  .refine((value) => !Number.isNaN(Number(value.replace(",", "."))), {
    message: "Le taux doit être numérique",
  })
  .refine((value) => {
    const numberValue = Number(value.replace(",", "."))
    return numberValue >= 0 && numberValue <= 100
  }, "Le taux doit être compris entre 0 et 100")

const configSchema = z
  .object({
    commission_rate_percent: percentSchema,
    insurance_commission_rate_percent: percentSchema,
    effective_from: z.string().min(1, "La date de début est requise"),
    effective_until: z.string().optional(),
  })
  .refine(
    (data) =>
      !data.effective_until || data.effective_until >= data.effective_from,
    {
      message: "La date de fin doit être après la date de début",
      path: ["effective_until"],
    },
  )

type ConfigFormData = z.infer<typeof configSchema>

interface CommissionConfigDialogProps {
  doctorId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  config: DoctorCommissionConfigPublic | null
}

export function CommissionConfigDialog({
  doctorId,
  open,
  onOpenChange,
  config,
}: CommissionConfigDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = config !== null
  const today = new Date().toISOString().slice(0, 10)
  const form = useForm<ConfigFormData>({
    resolver: zodResolver(configSchema),
    mode: "onBlur",
    defaultValues: {
      commission_rate_percent: "",
      insurance_commission_rate_percent: "",
      effective_from: today,
      effective_until: "",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      commission_rate_percent: decimalToPercentString(config?.commission_rate),
      insurance_commission_rate_percent: decimalToPercentString(
        config?.insurance_commission_rate,
      ),
      effective_from: config?.effective_from ?? today,
      effective_until: config?.effective_until ?? "",
    })
  }, [config, form, open, today])

  const mutation = useMutation({
    mutationFn: (data: ConfigFormData) => {
      const requestBody = {
        commission_rate: percentToDecimalString(data.commission_rate_percent),
        insurance_commission_rate: percentToDecimalString(
          data.insurance_commission_rate_percent,
        ),
        effective_until: data.effective_until || null,
      }
      if (isEdit) {
        return DoctorCommissionConfigsService.updateDoctorCommissionConfig({
          id: config.id,
          requestBody,
        })
      }
      return DoctorsService.createDoctorCommissionConfig({
        id: doctorId,
        requestBody: {
          ...requestBody,
          effective_from: data.effective_from,
        },
      })
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit
          ? "Configuration de commission mise à jour"
          : "Configuration de commission créée",
      )
      queryClient.invalidateQueries({
        queryKey: ["doctor-commission-configs", doctorId],
      })
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier la commission" : "Nouvelle commission"}
          </DialogTitle>
          <DialogDescription>
            Définissez les taux de commission applicables au médecin.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="commission_rate_percent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Commission directe (%)</FormLabel>
                    <FormControl>
                      <Input
                        inputMode="decimal"
                        placeholder="10,00"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="insurance_commission_rate_percent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Commission assurance (%)</FormLabel>
                    <FormControl>
                      <Input
                        inputMode="decimal"
                        placeholder="5,00"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="effective_from"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Début</FormLabel>
                    <FormControl>
                      <Input type="date" disabled={isEdit} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="effective_until"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fin</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
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
