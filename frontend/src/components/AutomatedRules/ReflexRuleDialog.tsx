import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Calculator } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { ReflexRuleDetailPublic } from "@/client"
import { AutomatedRulesService } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { SearchSelect } from "@/components/Common/SearchSelect"
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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { OPERATOR_LABELS } from "./labels"

const schema = z.object({
  trigger_analyte_id: z.string().min(1, "Analyte requis"),
  trigger_operator: z.enum(["gt", "gte", "lt", "lte", "eq", "in"]),
  trigger_value: z.string().min(1, "Valeur requise"),
  action_catalog_id: z.string().min(1, "Action requise"),
})

type FormData = z.infer<typeof schema>

interface ReflexRuleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule: ReflexRuleDetailPublic | null
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadCatalogOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ReflexRuleDialog({
  open,
  onOpenChange,
  rule,
  loadAnalyteOptions,
  loadCatalogOptions,
}: ReflexRuleDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [sampleValue, setSampleValue] = useState("")
  const [previewMessage, setPreviewMessage] = useState<string | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const isEdit = rule !== null
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      trigger_analyte_id: "",
      trigger_operator: "gt",
      trigger_value: "",
      action_catalog_id: "",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      trigger_analyte_id: rule?.trigger_analyte_id ?? "",
      trigger_operator: rule?.trigger_operator ?? "gt",
      trigger_value: rule?.trigger_value ?? "",
      action_catalog_id: rule?.action_catalog_id ?? "",
    })
    setSampleValue("")
    setPreviewMessage(null)
  }, [form, open, rule])

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      isEdit
        ? AutomatedRulesService.updateReflexRule({
            id: rule!.id,
            requestBody: data,
          })
        : AutomatedRulesService.createReflexRule({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast(isEdit ? "Règle mise à jour" : "Règle créée")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["automated-rules"] }),
  })

  const runPreview = async () => {
    const valid = await form.trigger(["trigger_operator", "trigger_value"])
    if (!valid) return
    setIsPreviewing(true)
    setPreviewMessage(null)
    try {
      const response = await AutomatedRulesService.previewReflexRule({
        requestBody: {
          trigger_operator: form.getValues("trigger_operator"),
          trigger_value: form.getValues("trigger_value"),
          sample_value: sampleValue,
        },
      })
      setPreviewMessage(response.message)
    } catch (err) {
      setPreviewMessage(errorMessage(err))
    } finally {
      setIsPreviewing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier la règle réflexe" : "Ajouter une règle réflexe"}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="trigger_analyte_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Analyte déclencheur</FormLabel>
                  <FormControl>
                    <SearchSelect
                      value={field.value || null}
                      selectedOption={
                        rule && field.value === rule.trigger_analyte_id
                          ? {
                              value: rule.trigger_analyte_id,
                              label: `${rule.trigger_analyte_code} - ${rule.trigger_analyte_name}`,
                            }
                          : null
                      }
                      onValueChange={(value) => field.onChange(value ?? "")}
                      loadOptions={loadAnalyteOptions}
                      placeholder="Sélectionner un analyte"
                      searchPlaceholder="Rechercher un analyte…"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-[160px_1fr]">
              <FormField
                control={form.control}
                name="trigger_operator"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Opérateur</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(OPERATOR_LABELS).map(
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
              <FormField
                control={form.control}
                name="trigger_value"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Valeur</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="ex. 5 ou Positif, Critique"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="action_catalog_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Action catalogue</FormLabel>
                  <FormControl>
                    <SearchSelect
                      value={field.value || null}
                      selectedOption={
                        rule && field.value === rule.action_catalog_id
                          ? {
                              value: rule.action_catalog_id,
                              label: `${rule.action_catalog_code} - ${rule.action_catalog_name}`,
                            }
                          : null
                      }
                      onValueChange={(value) => field.onChange(value ?? "")}
                      loadOptions={loadCatalogOptions}
                      placeholder="Sélectionner un test ou panel"
                      searchPlaceholder="Rechercher dans le catalogue…"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="rounded-md border bg-muted/20 p-3">
              <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                <Input
                  value={sampleValue}
                  onChange={(event) =>
                    setSampleValue(event.currentTarget.value)
                  }
                  placeholder="Valeur exemple à tester"
                />
                <LoadingButton
                  type="button"
                  variant="outline"
                  loading={isPreviewing}
                  onClick={runPreview}
                >
                  <Calculator className="size-4" />
                  Tester
                </LoadingButton>
              </div>
              {previewMessage && (
                <p className="mt-2 text-sm text-muted-foreground">
                  {previewMessage}
                </p>
              )}
            </div>

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

function errorMessage(error: unknown) {
  const maybeError = error as { body?: { detail?: string }; message?: string }
  return (
    maybeError.body?.detail ??
    maybeError.message ??
    "Prévisualisation impossible"
  )
}
