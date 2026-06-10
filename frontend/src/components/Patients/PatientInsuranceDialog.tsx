import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { PatientInsuranceWithProviderPublic } from "@/client"
import { InsuranceProvidersService, PatientsService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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

const insuranceSchema = z.object({
  insurance_provider_id: z.string().min(1, "L'assureur est requis"),
  policy_number: z.string().trim().min(1, "Le numéro de police est requis"),
  is_primary: z.boolean(),
})

type InsuranceFormData = z.infer<typeof insuranceSchema>

interface PatientInsuranceDialogProps {
  patientId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  insurance: PatientInsuranceWithProviderPublic | null
  onSaved?: (insurance: PatientInsuranceWithProviderPublic) => void
}

export function PatientInsuranceDialog({
  patientId,
  open,
  onOpenChange,
  insurance,
  onSaved,
}: PatientInsuranceDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = insurance !== null
  const [selectedProvider, setSelectedProvider] =
    useState<SearchSelectOption | null>(null)
  const form = useForm<InsuranceFormData>({
    resolver: zodResolver(insuranceSchema),
    mode: "onBlur",
    defaultValues: {
      insurance_provider_id: "",
      policy_number: "",
      is_primary: false,
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      insurance_provider_id: insurance?.insurance_provider_id ?? "",
      policy_number: insurance?.policy_number ?? "",
      is_primary: insurance?.is_primary ?? false,
    })
    setSelectedProvider(
      insurance
        ? {
            value: insurance.insurance_provider_id,
            label: insurance.insurance_provider_name,
          }
        : null,
    )
  }, [form, insurance, open])

  const loadProviderOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await InsuranceProvidersService.readInsuranceProviders({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((provider) => ({
        value: provider.id,
        label: provider.name,
      }))
    },
    [],
  )

  const mutation = useMutation({
    mutationFn: (data: InsuranceFormData) => {
      if (isEdit) {
        return PatientsService.updatePatientInsurance({
          id: patientId,
          insuranceId: insurance.id,
          requestBody: {
            policy_number: data.policy_number,
            is_primary: data.is_primary,
          },
        })
      }
      return PatientsService.createPatientInsurance({
        id: patientId,
        requestBody: data,
      })
    },
    onSuccess: (savedInsurance) => {
      showSuccessToast(isEdit ? "Assurance mise à jour" : "Assurance ajoutée")
      queryClient.invalidateQueries({
        queryKey: ["patient-insurance", patientId],
      })
      onSaved?.(savedInsurance)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier l'assurance" : "Ajouter une assurance"}
          </DialogTitle>
          <DialogDescription>
            Gérez la couverture utilisée lors de la création des demandes.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            <FormField
              control={form.control}
              name="insurance_provider_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Assureur *</FormLabel>
                  <FormControl>
                    <SearchSelect
                      value={field.value || null}
                      onValueChange={(value, option) => {
                        field.onChange(value ?? "")
                        setSelectedProvider(option ?? null)
                      }}
                      selectedOption={selectedProvider}
                      loadOptions={loadProviderOptions}
                      disabled={isEdit}
                      placeholder="Sélectionner un assureur"
                      searchPlaceholder="Rechercher un assureur…"
                      emptyMessage="Aucun assureur trouvé"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="policy_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Numéro de police *</FormLabel>
                  <FormControl>
                    <Input placeholder="ex. POL-2026-001" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="is_primary"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center gap-3 rounded-md border p-3">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={(checked) => field.onChange(!!checked)}
                    />
                  </FormControl>
                  <div className="space-y-0.5">
                    <FormLabel>Assurance principale</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Elle sera proposée par défaut à la création d'une demande.
                    </p>
                  </div>
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
                {isEdit ? "Enregistrer" : "Ajouter"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
