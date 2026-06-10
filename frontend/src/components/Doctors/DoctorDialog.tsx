import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { DoctorWithTitlePublic } from "@/client"
import { DoctorsService, TitlesService } from "@/client"
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
import { Switch } from "@/components/ui/switch"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { percentToDecimalString } from "./utils"

const doctorSchema = z
  .object({
    first_name: z.string().trim().min(1, "Le prénom est requis"),
    last_name: z.string().trim().min(1, "Le nom est requis"),
    provenance: z.string().trim().optional(),
    phone: z.string().trim().optional(),
    title_id: z.string().nullable(),
    configure_commission: z.boolean(),
    commission_rate_percent: z.string(),
    insurance_commission_rate_percent: z.string(),
    effective_from: z.string(),
    effective_until: z.string(),
  })
  .superRefine((data, context) => {
    if (!data.configure_commission) return
    for (const [path, value] of [
      ["commission_rate_percent", data.commission_rate_percent],
      [
        "insurance_commission_rate_percent",
        data.insurance_commission_rate_percent,
      ],
    ] as const) {
      const parsed = Number(value.replace(",", "."))
      if (!value || Number.isNaN(parsed) || parsed < 0 || parsed > 100) {
        context.addIssue({
          code: "custom",
          path: [path],
          message: "Le taux doit être compris entre 0 et 100",
        })
      }
    }
    if (!data.effective_from) {
      context.addIssue({
        code: "custom",
        path: ["effective_from"],
        message: "La date de début est requise",
      })
    }
    if (data.effective_until && data.effective_until < data.effective_from) {
      context.addIssue({
        code: "custom",
        path: ["effective_until"],
        message: "La date de fin doit suivre la date de début",
      })
    }
  })

type DoctorFormData = z.infer<typeof doctorSchema>

interface DoctorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  doctor: DoctorWithTitlePublic | null
  allowCommissionConfig?: boolean
  onSaved?: (doctor: DoctorWithTitlePublic) => void
}

export function DoctorDialog({
  open,
  onOpenChange,
  doctor,
  allowCommissionConfig = false,
  onSaved,
}: DoctorDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = doctor !== null
  const [selectedTitle, setSelectedTitle] = useState<SearchSelectOption | null>(
    null,
  )
  const form = useForm<DoctorFormData>({
    resolver: zodResolver(doctorSchema),
    mode: "onBlur",
    defaultValues: {
      first_name: "",
      last_name: "",
      provenance: "",
      phone: "",
      title_id: null,
      configure_commission: false,
      commission_rate_percent: "",
      insurance_commission_rate_percent: "",
      effective_from: new Date().toISOString().slice(0, 10),
      effective_until: "",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      first_name: doctor?.first_name ?? "",
      last_name: doctor?.last_name ?? "",
      provenance: doctor?.provenance ?? "",
      phone: doctor?.phone ?? "",
      title_id: doctor?.title_id ?? null,
      configure_commission: false,
      commission_rate_percent: "",
      insurance_commission_rate_percent: "",
      effective_from: new Date().toISOString().slice(0, 10),
      effective_until: "",
    })
    setSelectedTitle(
      doctor?.title_id
        ? {
            value: doctor.title_id,
            label: doctor.title_name ?? doctor.title_id,
          }
        : null,
    )
  }, [doctor, form, open])

  const loadTitleOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await TitlesService.readTitles({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((title) => ({
        value: title.id,
        label: title.name,
      }))
    },
    [],
  )

  const mutation = useMutation({
    mutationFn: async (data: DoctorFormData) => {
      const requestBody = {
        first_name: data.first_name,
        last_name: data.last_name,
        provenance: data.provenance || null,
        phone: data.phone || null,
        title_id: data.title_id || null,
      }
      if (isEdit) {
        return {
          savedDoctor: await DoctorsService.updateDoctor({
            id: doctor.id,
            requestBody,
          }),
          commissionFailed: false,
        }
      }
      const savedDoctor = await DoctorsService.createDoctor({ requestBody })
      if (allowCommissionConfig && data.configure_commission) {
        try {
          await DoctorsService.createDoctorCommissionConfig({
            id: savedDoctor.id,
            requestBody: {
              commission_rate: percentToDecimalString(
                data.commission_rate_percent,
              ),
              insurance_commission_rate: percentToDecimalString(
                data.insurance_commission_rate_percent,
              ),
              effective_from: data.effective_from,
              effective_until: data.effective_until || null,
            },
          })
        } catch {
          return { savedDoctor, commissionFailed: true }
        }
      }
      return { savedDoctor, commissionFailed: false }
    },
    onSuccess: ({ savedDoctor, commissionFailed }) => {
      showSuccessToast(isEdit ? "Médecin mis à jour" : "Médecin créé")
      if (commissionFailed) {
        showErrorToast(
          "Le médecin a été créé, mais sa commission n'a pas pu être enregistrée.",
        )
      }
      queryClient.invalidateQueries({ queryKey: ["doctors"] })
      queryClient.invalidateQueries({ queryKey: ["doctor", savedDoctor.id] })
      onSaved?.(savedDoctor)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le médecin" : "Nouveau médecin"}
          </DialogTitle>
          <DialogDescription>
            Renseignez les informations du médecin prescripteur.
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
                name="title_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Titre</FormLabel>
                    <FormControl>
                      <SearchSelect
                        value={field.value}
                        onValueChange={(value, option) => {
                          field.onChange(value)
                          setSelectedTitle(option ?? null)
                        }}
                        selectedOption={selectedTitle}
                        loadOptions={loadTitleOptions}
                        placeholder="Sélectionner un titre"
                        searchPlaceholder="Rechercher un titre…"
                        emptyMessage="Aucun titre trouvé"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Téléphone</FormLabel>
                    <FormControl>
                      <Input placeholder="+223 ..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Prénom *</FormLabel>
                    <FormControl>
                      <Input placeholder="Prénom" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nom *</FormLabel>
                    <FormControl>
                      <Input placeholder="Nom" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="provenance"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provenance</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Cabinet, service ou établissement"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {!isEdit && allowCommissionConfig && (
              <div className="space-y-4 border-t pt-4">
                <FormField
                  control={form.control}
                  name="configure_commission"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between gap-4">
                      <div>
                        <FormLabel>Configurer la commission</FormLabel>
                        <p className="text-xs text-muted-foreground">
                          Définir les taux applicables dès cette demande.
                        </p>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                {form.watch("configure_commission") && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="commission_rate_percent"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Commission directe (%) *</FormLabel>
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
                          <FormLabel>Commission assurance (%) *</FormLabel>
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
                          <FormLabel>Début *</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
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
                )}
              </div>
            )}
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
