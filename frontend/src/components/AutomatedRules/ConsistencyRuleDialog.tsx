import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { X } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { ConsistencyRuleDetailPublic } from "@/client"
import { AutomatedRulesService } from "@/client"
import { FormulaBuilder } from "@/components/Common/FormulaBuilder"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { SearchSelect } from "@/components/Common/SearchSelect"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
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
import { SEVERITY_LABELS } from "./labels"

const schema = z.object({
  name: z.string().min(1, "Le nom est requis"),
  formula: z.string().min(1, "La formule est requise"),
  formula_description: z.string().optional(),
  error_message: z.string().min(1, "Le message est requis"),
  severity: z.enum(["warning", "error"]),
})

type FormData = z.infer<typeof schema>

interface ConsistencyRuleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule: ConsistencyRuleDetailPublic | null
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ConsistencyRuleDialog({
  open,
  onOpenChange,
  rule,
  loadAnalyteOptions,
}: ConsistencyRuleDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selectedAnalytes, setSelectedAnalytes] = useState<
    SearchSelectOption[]
  >([])
  const [pickerValue, setPickerValue] = useState<string | null>(null)
  const isEdit = rule !== null
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      formula: "",
      formula_description: "",
      error_message: "",
      severity: "warning",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      name: rule?.name ?? "",
      formula: rule?.formula ?? "",
      formula_description: rule?.formula_description ?? "",
      error_message: rule?.error_message ?? "",
      severity: rule?.severity ?? "warning",
    })
    setSelectedAnalytes(
      (rule?.analytes ?? []).map((analyte) => ({
        value: analyte.id,
        label: `${analyte.code} - ${analyte.name}`,
        description: `${analyte.code} · ${analyte.name}`,
      })),
    )
  }, [form, open, rule])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const requestBody = {
        name: data.name.trim(),
        formula: data.formula.trim(),
        formula_description: data.formula_description?.trim() || null,
        error_message: data.error_message.trim(),
        severity: data.severity,
        analyte_ids: selectedAnalytes.map((item) => item.value),
      }
      return isEdit
        ? AutomatedRulesService.updateConsistencyRule({
            id: rule!.id,
            requestBody,
          })
        : AutomatedRulesService.createConsistencyRule({ requestBody })
    },
    onSuccess: () => {
      showSuccessToast(isEdit ? "Règle mise à jour" : "Règle créée")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })

  const addAnalyte = (_value: string | null, option?: SearchSelectOption) => {
    if (!option) return
    setSelectedAnalytes((current) =>
      current.some((item) => item.value === option.value)
        ? current
        : [...current, option],
    )
    setPickerValue(null)
  }

  const removeAnalyte = (id: string) => {
    setSelectedAnalytes((current) =>
      current.filter((item) => item.value !== id),
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit
              ? "Modifier la règle de cohérence"
              : "Ajouter une règle de cohérence"}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nom</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="severity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sévérité</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(SEVERITY_LABELS).map(
                          ([value, label]) => (
                            <SelectItem key={value} value={value}>
                              {label}
                            </SelectItem>
                          ),
                        )}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-2">
              <FormLabel>Analytes concernés</FormLabel>
              <SearchSelect
                value={pickerValue}
                onValueChange={addAnalyte}
                loadOptions={loadAnalyteOptions}
                placeholder="Ajouter un analyte"
                searchPlaceholder="Rechercher un analyte…"
              />
              <div className="flex min-h-9 flex-wrap gap-1.5 rounded-md border bg-muted/20 p-2">
                {selectedAnalytes.length === 0 ? (
                  <span className="text-sm text-muted-foreground">
                    Aucun analyte sélectionné
                  </span>
                ) : (
                  selectedAnalytes.map((analyte) => (
                    <Badge
                      key={analyte.value}
                      variant="secondary"
                      className="gap-1"
                    >
                      {analyte.label}
                      <button
                        type="button"
                        onClick={() => removeAnalyte(analyte.value)}
                      >
                        <X className="size-3" />
                      </button>
                    </Badge>
                  ))
                )}
              </div>
            </div>

            <FormField
              control={form.control}
              name="formula"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Formule</FormLabel>
                  <FormControl>
                    <FormulaBuilder
                      value={field.value}
                      onChange={field.onChange}
                      expectedResultType="boolean"
                      loadAnalyteOptions={loadAnalyteOptions}
                      previewFormula={(formula, values) =>
                        AutomatedRulesService.previewConsistencyRule({
                          requestBody: {
                            formula,
                            analyte_ids: selectedAnalytes.map(
                              (item) => item.value,
                            ),
                            values,
                          },
                        })
                      }
                      placeholder="{GLU} / {INS} > 0.85"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="formula_description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea rows={2} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="error_message"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Message affiché</FormLabel>
                  <FormControl>
                    <Textarea rows={2} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Annuler</Button>
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
