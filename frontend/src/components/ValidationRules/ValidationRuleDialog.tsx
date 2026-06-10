import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import type { TargetGenderType, ValidationRuleDetailPublic } from "@/client"
import { AnalytesService, ValidationRulesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { NONE, type RuleFormState } from "./types"
import { buildPayload, emptyRuleForm, ruleToForm } from "./utils"
import {
  DecimalField,
  NumberField,
  OptionTextarea,
  TextField,
} from "./ValidationRuleFields"

interface ValidationRuleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule: ValidationRuleDetailPublic | null
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadContextOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ValidationRuleDialog({
  open,
  onOpenChange,
  rule,
  loadAnalyteOptions,
  loadContextOptions,
}: ValidationRuleDialogProps) {
  const canManage = usePermission("rules", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [form, setForm] = useState<RuleFormState>(emptyRuleForm)

  useEffect(() => {
    if (open) setForm(rule ? ruleToForm(rule) : emptyRuleForm())
  }, [open, rule])

  const analyteQuery = useQuery({
    queryKey: ["analytes", "detail", form.analyteId],
    queryFn: () => AnalytesService.readAnalyte({ id: form.analyteId }),
    enabled: open && !!form.analyteId,
  })
  const selectedAnalyte = analyteQuery.data
  const dataType = selectedAnalyte?.data_type ?? rule?.analyte_data_type
  const optionValues = Array.isArray(selectedAnalyte?.options_data)
    ? selectedAnalyte.options_data.filter(
        (item): item is string => typeof item === "string",
      )
    : []

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = buildPayload(form)
      if (rule) {
        await ValidationRulesService.updateValidationRule({
          id: rule.id,
          requestBody: payload,
        })
      } else {
        await ValidationRulesService.createValidationRule({
          requestBody: payload,
        })
      }
    },
    onSuccess: () => {
      showSuccessToast(rule ? "Règle mise à jour" : "Règle créée")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["validation-rules"] }),
  })

  if (!canManage) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>
            {rule ? "Modifier la règle" : "Ajouter une règle"}
          </DialogTitle>
          <DialogDescription>
            Définissez la population cible et les contrôles selon le type
            d'analyte.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-5 py-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label>Analyte</Label>
              <SearchSelect
                value={form.analyteId || null}
                selectedOption={
                  form.analyteLabel
                    ? { value: form.analyteId, label: form.analyteLabel }
                    : null
                }
                onValueChange={(value, option) =>
                  setForm({
                    ...form,
                    analyteId: value ?? "",
                    analyteLabel: option?.label ?? "",
                  })
                }
                loadOptions={loadAnalyteOptions}
                placeholder="Sélectionner un analyte"
                searchPlaceholder="Rechercher un analyte…"
                emptyMessage="Aucun analyte"
              />
            </div>
            <div className="grid gap-2">
              <Label>Contexte patient</Label>
              <SearchSelect
                value={form.contextId === NONE ? null : form.contextId}
                selectedOption={
                  form.contextId !== NONE && form.contextLabel
                    ? { value: form.contextId, label: form.contextLabel }
                    : null
                }
                onValueChange={(value, option) =>
                  setForm({
                    ...form,
                    contextId: value ?? NONE,
                    contextLabel: option?.label ?? "",
                  })
                }
                loadOptions={loadContextOptions}
                placeholder="Tous les contextes"
                searchPlaceholder="Rechercher un contexte…"
                emptyMessage="Aucun contexte"
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-5">
            <div className="grid gap-2">
              <Label>Genre</Label>
              <Select
                value={form.targetGender}
                onValueChange={(value) =>
                  setForm({ ...form, targetGender: value as TargetGenderType })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="male">Homme</SelectItem>
                  <SelectItem value="female">Femme</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <NumberField
              label="Âge min"
              value={form.minAgeYears}
              onChange={(value) => setForm({ ...form, minAgeYears: value })}
            />
            <NumberField
              label="Âge max"
              value={form.maxAgeYears}
              onChange={(value) => setForm({ ...form, maxAgeYears: value })}
            />
            <NumberField
              label="Priorité"
              value={form.priority}
              onChange={(value) => setForm({ ...form, priority: value })}
            />
            <div className="grid gap-2">
              <Label>Active</Label>
              <div className="flex h-10 items-center">
                <Switch
                  checked={form.isActive}
                  onCheckedChange={(value) =>
                    setForm({ ...form, isActive: value })
                  }
                />
              </div>
            </div>
          </div>

          {dataType === "numeric" && (
            <div className="grid gap-4 md:grid-cols-4">
              <DecimalField
                label="Normal min"
                value={form.normalMin}
                onChange={(value) => setForm({ ...form, normalMin: value })}
              />
              <DecimalField
                label="Normal max"
                value={form.normalMax}
                onChange={(value) => setForm({ ...form, normalMax: value })}
              />
              <DecimalField
                label="Panique min"
                value={form.panicMin}
                onChange={(value) => setForm({ ...form, panicMin: value })}
              />
              <DecimalField
                label="Panique max"
                value={form.panicMax}
                onChange={(value) => setForm({ ...form, panicMax: value })}
              />
              <DecimalField
                label="Absurde min"
                value={form.absurdMin}
                onChange={(value) => setForm({ ...form, absurdMin: value })}
              />
              <DecimalField
                label="Absurde max"
                value={form.absurdMax}
                onChange={(value) => setForm({ ...form, absurdMax: value })}
              />
              <DecimalField
                label="Valeur attendue"
                value={form.expectedValue}
                onChange={(value) => setForm({ ...form, expectedValue: value })}
              />
              <DecimalField
                label="Delta max %"
                value={form.maxDeltaPercent}
                onChange={(value) =>
                  setForm({ ...form, maxDeltaPercent: value })
                }
              />
            </div>
          )}

          {dataType === "text" && (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label>Texte obligatoire</Label>
                <div className="flex h-10 items-center">
                  <Switch
                    checked={form.isRequired}
                    onCheckedChange={(value) =>
                      setForm({ ...form, isRequired: value })
                    }
                  />
                </div>
              </div>
              <TextField
                label="Regex"
                value={form.regexPattern}
                onChange={(value) => setForm({ ...form, regexPattern: value })}
                placeholder="^[A-Z]{3}$"
              />
              <div className="grid gap-2 md:col-span-2">
                <Label>Message de validation</Label>
                <Textarea
                  value={form.validationMessage}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      validationMessage: event.currentTarget.value,
                    })
                  }
                  rows={3}
                />
              </div>
            </div>
          )}

          {dataType === "options" && (
            <div className="grid gap-4 md:grid-cols-3">
              <OptionTextarea
                label="Valeurs autorisées"
                value={form.allowedValues}
                onChange={(value) => setForm({ ...form, allowedValues: value })}
                options={optionValues}
              />
              <OptionTextarea
                label="Valeurs anormales"
                value={form.abnormalValues}
                onChange={(value) =>
                  setForm({ ...form, abnormalValues: value })
                }
                options={optionValues}
              />
              <OptionTextarea
                label="Valeurs critiques"
                value={form.criticalValues}
                onChange={(value) =>
                  setForm({ ...form, criticalValues: value })
                }
                options={optionValues}
              />
            </div>
          )}

          {dataType === "image" && (
            <div className="grid gap-2">
              <Label>Image obligatoire</Label>
              <div className="flex h-10 items-center">
                <Switch
                  checked={form.isRequired}
                  onCheckedChange={(value) =>
                    setForm({ ...form, isRequired: value })
                  }
                />
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <LoadingButton
            loading={mutation.isPending}
            disabled={!form.analyteId}
            onClick={() => mutation.mutate()}
          >
            {rule ? "Enregistrer" : "Créer la règle"}
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
