import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { AnalyteDataType, AnalytePublic } from "@/client"
import { AnalytesService, FormulasService, UnitsService } from "@/client"
import { FormulaBuilder } from "@/components/Common/FormulaBuilder"
import { RichTextEditor } from "@/components/Common/RichTextEditor"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { DATA_TYPE_LABELS, DATA_TYPE_OPTIONS } from "./labels"

const NO_UNIT = "__none__"

const formSchema = z
  .object({
    code: z.string().min(1, "Le code est requis"),
    name: z.string().min(1, "Le nom est requis"),
    unit_id: z.string(),
    data_type: z.enum(["numeric", "text", "options", "image"]),
    options_text: z.string().optional(),
    reference_text: z.string().optional(),
    is_calculated: z.boolean(),
    calculation_formula: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.data_type === "options") {
      const options = parseOptions(data.options_text)
      if (options.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["options_text"],
          message: "Ajoutez au moins une option",
        })
      }
    }
    if (data.is_calculated && !data.calculation_formula?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["calculation_formula"],
        message: "La formule de calcul est requise",
      })
    }
  })

type FormData = z.infer<typeof formSchema>

interface AnalyteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  analyte: AnalytePublic | null
}

function parseOptions(value: string | undefined): string[] {
  return (value ?? "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
}

function optionsToText(optionsData: unknown): string {
  if (!Array.isArray(optionsData)) return ""
  return optionsData.filter((item) => typeof item === "string").join("\n")
}

export function AnalyteDialog({
  open,
  onOpenChange,
  analyte,
}: AnalyteDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = analyte !== null

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      code: "",
      name: "",
      unit_id: NO_UNIT,
      data_type: "numeric",
      options_text: "",
      reference_text: "",
      is_calculated: false,
      calculation_formula: "",
    },
  })

  const dataType = form.watch("data_type")
  const isCalculated = form.watch("is_calculated")
  const unitId = form.watch("unit_id")

  const selectedUnitQuery = useQuery({
    queryKey: ["units", "detail", unitId],
    queryFn: () => UnitsService.readUnit({ id: unitId }),
    enabled: open && unitId !== NO_UNIT,
  })

  const loadUnitOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await UnitsService.readUnits({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((unit) => ({
        value: unit.id,
        label: unit.name,
      }))
    },
    [],
  )

  const loadAnalyteOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await AnalytesService.readAnalytes({
        search: query || undefined,
        dataType: "numeric",
        limit: 20,
      })
      return response.data
        .filter((item) => item.id !== analyte?.id)
        .map((item) => ({
          value: item.id,
          label: `${item.code} - ${item.name}`,
          description: `${item.code} · ${item.name}`,
        }))
    },
    [analyte?.id],
  )

  useEffect(() => {
    if (open) {
      form.reset({
        code: analyte?.code ?? "",
        name: analyte?.name ?? "",
        unit_id: analyte?.unit_id ?? NO_UNIT,
        data_type: analyte?.data_type ?? "numeric",
        options_text: optionsToText(analyte?.options_data),
        reference_text: analyte?.reference_text ?? "",
        is_calculated: analyte?.is_calculated ?? false,
        calculation_formula: analyte?.calculation_formula ?? "",
      })
    }
  }, [open, analyte, form])

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      const body = {
        code: data.code.trim().toUpperCase(),
        name: data.name.trim(),
        unit_id: data.unit_id === NO_UNIT ? null : data.unit_id,
        data_type: data.data_type as AnalyteDataType,
        options_data:
          data.data_type === "options" ? parseOptions(data.options_text) : null,
        reference_text: data.reference_text || null,
        is_calculated: data.is_calculated,
        calculation_formula: data.is_calculated
          ? data.calculation_formula?.trim() || null
          : null,
      }

      if (isEdit) {
        await AnalytesService.updateAnalyte({
          id: analyte!.id,
          requestBody: body,
        })
      } else {
        await AnalytesService.createAnalyte({ requestBody: body })
      }
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit ? "Analyte mis à jour avec succès" : "Analyte créé avec succès",
      )
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["analytes"] })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier l'analyte" : "Ajouter un analyte"}
          </DialogTitle>
          <DialogDescription>
            Définissez le code, le type de résultat et les références affichées
            pendant la saisie des résultats.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Code <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="ex. GLU"
                          type="text"
                          {...field}
                          onChange={(e) =>
                            field.onChange(e.currentTarget.value.toUpperCase())
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
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
                          placeholder="ex. Glucose"
                          type="text"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="data_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Type de résultat</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {DATA_TYPE_OPTIONS.map((type) => (
                            <SelectItem key={type} value={type}>
                              {DATA_TYPE_LABELS[type]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="unit_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Unité</FormLabel>
                      <FormControl>
                        <SearchSelect
                          value={field.value === NO_UNIT ? null : field.value}
                          selectedOption={
                            field.value === NO_UNIT || !selectedUnitQuery.data
                              ? null
                              : {
                                  value: selectedUnitQuery.data.id,
                                  label: selectedUnitQuery.data.name,
                                }
                          }
                          onValueChange={(value) =>
                            field.onChange(value ?? NO_UNIT)
                          }
                          loadOptions={loadUnitOptions}
                          placeholder="Aucune unité"
                          searchPlaceholder="Rechercher une unité…"
                          emptyMessage="Aucune unité"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {dataType === "options" && (
                <FormField
                  control={form.control}
                  name="options_text"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Options</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder={"Positif\nNégatif"}
                          rows={4}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="reference_text"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Référence</FormLabel>
                    <FormControl>
                      <RichTextEditor
                        value={field.value}
                        onChange={field.onChange}
                        placeholder="Ajoutez les références ou commentaires d'interprétation…"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_calculated"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center gap-3 rounded-md border p-3">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={(checked) =>
                          field.onChange(checked === true)
                        }
                      />
                    </FormControl>
                    <div>
                      <FormLabel>Analyte calculé</FormLabel>
                      <p className="text-sm text-muted-foreground">
                        Utiliser une formule pour calculer automatiquement ce
                        résultat.
                      </p>
                    </div>
                  </FormItem>
                )}
              />

              {isCalculated && (
                <FormField
                  control={form.control}
                  name="calculation_formula"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Formule de calcul</FormLabel>
                      <FormControl>
                        <FormulaBuilder
                          value={field.value ?? ""}
                          onChange={field.onChange}
                          expectedResultType="number"
                          loadAnalyteOptions={loadAnalyteOptions}
                          previewFormula={(formula, values) =>
                            FormulasService.previewFormula({
                              requestBody: {
                                formula,
                                expected_result_type: "number",
                                values,
                              },
                            })
                          }
                          placeholder="{GLU} / {CREAT}"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
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
