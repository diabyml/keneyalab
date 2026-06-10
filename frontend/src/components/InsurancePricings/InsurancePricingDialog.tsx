import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { InsurancePricingDetailPublic } from "@/client"
import { InsurancePricingsService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
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

const priceSchema = z
  .string()
  .trim()
  .min(1, "Le prix est requis")
  .refine((value) => !Number.isNaN(Number(value.replace(",", "."))), {
    message: "Le prix doit être numérique",
  })
  .refine((value) => Number(value.replace(",", ".")) >= 0, {
    message: "Le prix doit être positif",
  })

const pricingSchema = z.object({
  insurance_provider_id: z.string().min(1, "L'assureur est requis"),
  catalog_id: z.string().min(1, "Le test est requis"),
  insurance_price: priceSchema,
})

type PricingFormData = z.infer<typeof pricingSchema>

interface InsurancePricingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pricing: InsurancePricingDetailPublic | null
  providerOption: SearchSelectOption | null
  catalogOption: SearchSelectOption | null
  onProviderOptionChange: (option: SearchSelectOption | null) => void
  onCatalogOptionChange: (option: SearchSelectOption | null) => void
  loadProviderOptions: (query: string) => Promise<SearchSelectOption[]>
  loadCatalogOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function InsurancePricingDialog({
  open,
  onOpenChange,
  pricing,
  providerOption,
  catalogOption,
  onProviderOptionChange,
  onCatalogOptionChange,
  loadProviderOptions,
  loadCatalogOptions,
}: InsurancePricingDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = pricing !== null
  const form = useForm<PricingFormData>({
    resolver: zodResolver(pricingSchema),
    mode: "onBlur",
    defaultValues: {
      insurance_provider_id: "",
      catalog_id: "",
      insurance_price: "",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      insurance_provider_id: pricing?.insurance_provider_id ?? "",
      catalog_id: pricing?.catalog_id ?? "",
      insurance_price: pricing
        ? Number(pricing.insurance_price).toFixed(2)
        : "",
    })
    onProviderOptionChange(
      pricing
        ? {
            value: pricing.insurance_provider_id,
            label: pricing.insurance_provider_name,
          }
        : null,
    )
    onCatalogOptionChange(
      pricing
        ? {
            value: pricing.catalog_id,
            label: `${pricing.catalog_code} · ${pricing.catalog_name}`,
          }
        : null,
    )
  }, [form, onCatalogOptionChange, onProviderOptionChange, open, pricing])

  const mutation = useMutation({
    mutationFn: (data: PricingFormData) => {
      const requestBody = {
        insurance_price: Number(data.insurance_price.replace(",", ".")).toFixed(
          2,
        ),
      }
      if (pricing) {
        return InsurancePricingsService.updateInsurancePricing({
          id: pricing.id,
          requestBody,
        })
      }
      return InsurancePricingsService.createInsurancePricing({
        requestBody: {
          ...requestBody,
          insurance_provider_id: data.insurance_provider_id,
          catalog_id: data.catalog_id,
        },
      })
    },
    onSuccess: () => {
      showSuccessToast(
        pricing ? "Tarif assurance mis à jour" : "Tarif assurance créé",
      )
      queryClient.invalidateQueries({ queryKey: ["insurance-pricings"] })
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le tarif assurance" : "Nouveau tarif assurance"}
          </DialogTitle>
          <DialogDescription>
            Définissez le prix facturé pour un test chez un assureur.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            <div className="grid gap-4 md:grid-cols-2">
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
                          onProviderOptionChange(option ?? null)
                        }}
                        selectedOption={providerOption}
                        loadOptions={loadProviderOptions}
                        disabled={isEdit}
                        placeholder="Sélectionner un assureur"
                        searchPlaceholder="Rechercher un assureur…"
                        emptyMessage="Aucun assureur"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="catalog_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Test *</FormLabel>
                    <FormControl>
                      <SearchSelect
                        value={field.value || null}
                        onValueChange={(value, option) => {
                          field.onChange(value ?? "")
                          onCatalogOptionChange(option ?? null)
                        }}
                        selectedOption={catalogOption}
                        loadOptions={loadCatalogOptions}
                        disabled={isEdit}
                        placeholder="Sélectionner un test"
                        searchPlaceholder="Rechercher un test…"
                        emptyMessage="Aucun test"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="insurance_price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Prix assurance *</FormLabel>
                    <FormControl>
                      <Input
                        inputMode="decimal"
                        placeholder="0,00"
                        {...field}
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
