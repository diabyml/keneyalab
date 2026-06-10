import { useMutation } from "@tanstack/react-query"
import { FlaskConical } from "lucide-react"
import { useState } from "react"

import type { GenderType, ValidationRuleSimulationResponse } from "@/client"
import { ValidationRulesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { NONE, type SimulatorState } from "./types"
import { normalizeDecimalInput, nullableNumber } from "./utils"
import { NumberField, TextField } from "./ValidationRuleFields"
import { FilterSelect } from "./ValidationRuleFilters"

interface ValidationSimulatorSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadContextOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ValidationSimulatorSheet({
  open,
  onOpenChange,
  loadAnalyteOptions,
  loadContextOptions,
}: ValidationSimulatorSheetProps) {
  const canManage = usePermission("rules", "manage")

  if (!canManage) return null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <FlaskConical className="size-5" />
            Simulateur
          </SheetTitle>
          <SheetDescription>
            Testez le matching et la classification d'un résultat.
          </SheetDescription>
        </SheetHeader>
        <ValidationSimulator
          loadAnalyteOptions={loadAnalyteOptions}
          loadContextOptions={loadContextOptions}
        />
      </SheetContent>
    </Sheet>
  )
}

function emptySimulator(): SimulatorState {
  return {
    analyteId: "",
    analyteLabel: "",
    gender: NONE,
    ageYears: "",
    contextId: NONE,
    contextLabel: "",
    resultValue: "",
    previousValue: "",
  }
}

function ValidationSimulator({
  loadAnalyteOptions,
  loadContextOptions,
}: {
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadContextOptions: (query: string) => Promise<SearchSelectOption[]>
}) {
  const { showErrorToast } = useCustomToast()
  const [form, setForm] = useState<SimulatorState>(emptySimulator)
  const [result, setResult] = useState<ValidationRuleSimulationResponse | null>(
    null,
  )

  const mutation = useMutation({
    mutationFn: () =>
      ValidationRulesService.simulateValidationRule({
        requestBody: {
          analyte_id: form.analyteId,
          gender: form.gender === NONE ? null : (form.gender as GenderType),
          age_years: nullableNumber(form.ageYears),
          patient_context_id: form.contextId === NONE ? null : form.contextId,
          result_value: normalizeDecimalInput(form.resultValue),
          previous_value: normalizeDecimalInput(form.previousValue),
        },
      }),
    onMutate: () => setResult(null),
    onSuccess: setResult,
    onError: (error) => {
      setResult(null)
      handleError.call(
        showErrorToast,
        error as Parameters<typeof handleError>[0],
      )
    },
  })

  return (
    <div className="grid gap-4 px-4 pb-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2 md:col-span-2">
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
        <FilterSelect
          label="Genre"
          value={form.gender}
          onValueChange={(value) => setForm({ ...form, gender: value })}
          options={[
            [NONE, "Non précisé"],
            ["male", "Homme"],
            ["female", "Femme"],
          ]}
          triggerClassName="w-full"
        />
        <NumberField
          label="Âge"
          value={form.ageYears}
          onChange={(value) => setForm({ ...form, ageYears: value })}
        />
        <div className="grid gap-2 md:col-span-2">
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
            placeholder="Aucun contexte"
            searchPlaceholder="Rechercher un contexte…"
            emptyMessage="Aucun contexte"
          />
        </div>
        <TextField
          label="Résultat"
          value={form.resultValue}
          onChange={(value) => setForm({ ...form, resultValue: value })}
          inputMode="decimal"
        />
        <TextField
          label="Résultat précédent"
          value={form.previousValue}
          onChange={(value) => setForm({ ...form, previousValue: value })}
          inputMode="decimal"
        />
      </div>

      <div className="flex items-center gap-2">
        <LoadingButton
          loading={mutation.isPending}
          disabled={!form.analyteId}
          onClick={() => mutation.mutate()}
        >
          Simuler
        </LoadingButton>
        <Button
          variant="ghost"
          onClick={() => {
            setForm(emptySimulator())
            setResult(null)
          }}
        >
          Réinitialiser
        </Button>
      </div>

      {result && (
        <div className="rounded-lg border bg-muted/20 p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant={result.is_valid ? "secondary" : "destructive"}>
              {result.classification}
            </Badge>
            {result.is_abnormal && <Badge variant="outline">Anormal</Badge>}
            {result.is_critical && <Badge variant="outline">Critique</Badge>}
            {result.is_absurd && <Badge variant="destructive">Absurde</Badge>}
            {result.delta_flag && <Badge variant="outline">Delta</Badge>}
          </div>
          <div className="text-sm">{result.message}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {result.matched_rule
              ? `Règle: ${result.matched_rule.analyte_code}, priorité ${result.matched_rule.priority ?? 0}`
              : "Aucune règle applicable"}
          </div>
        </div>
      )}
    </div>
  )
}
