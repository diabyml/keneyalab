import { useState } from "react"

import type {
  ConsistencyRuleDetailPublic,
  FormulaResultType,
  ReflexRuleDetailPublic,
} from "@/client"
import { AutomatedRulesService } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { formatDecimal } from "@/lib/format"
import { OPERATOR_LABELS } from "./labels"

type PreviewTarget =
  | { type: "consistency"; rule: ConsistencyRuleDetailPublic }
  | { type: "reflex"; rule: ReflexRuleDetailPublic }
  | null

interface AutomatedRulePreviewSheetProps {
  target: PreviewTarget
  onOpenChange: (open: boolean) => void
}

export function AutomatedRulePreviewSheet({
  target,
  onOpenChange,
}: AutomatedRulePreviewSheetProps) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [sampleValue, setSampleValue] = useState("")
  const [message, setMessage] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [resultType, setResultType] = useState<FormulaResultType | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const open = target !== null

  const runPreview = async () => {
    if (!target) return
    setIsLoading(true)
    setMessage(null)
    setResult(null)
    setResultType(null)
    try {
      if (target.type === "consistency") {
        const response = await AutomatedRulesService.previewConsistencyRule({
          requestBody: {
            formula: target.rule.formula,
            analyte_ids: (target.rule.analytes ?? []).map((item) => item.id),
            values,
          },
        })
        setMessage(response.message)
        setResult(response.result ?? null)
        setResultType(response.result_type ?? null)
      } else {
        const response = await AutomatedRulesService.previewReflexRule({
          requestBody: {
            trigger_operator: target.rule.trigger_operator,
            trigger_value: target.rule.trigger_value,
            sample_value: sampleValue,
          },
        })
        setMessage(response.message)
      }
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Sheet
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          setValues({})
          setSampleValue("")
          setMessage(null)
          setResult(null)
          setResultType(null)
        }
        onOpenChange(nextOpen)
      }}
    >
      <SheetContent className="w-full p-4 overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>Tester la règle</SheetTitle>
          <SheetDescription>
            Saisissez des valeurs exemple pour vérifier le comportement.
          </SheetDescription>
        </SheetHeader>
        {target?.type === "consistency" && (
          <div className="mt-6 space-y-4">
            <div>
              <div className="font-medium">{target.rule.name}</div>
              <div className="mt-1 rounded-md bg-muted p-3 font-mono text-sm">
                {target.rule.formula}
              </div>
            </div>
            <div className="grid gap-3">
              {(target.rule.analytes ?? []).map((analyte) => (
                <div key={analyte.id} className="grid gap-1">
                  <label
                    htmlFor={`rule-preview-${analyte.id}`}
                    className="text-sm font-medium"
                  >
                    {analyte.code} · {analyte.name}
                  </label>
                  <Input
                    id={`rule-preview-${analyte.id}`}
                    value={values[analyte.code] ?? ""}
                    onChange={(event) => {
                      const nextValue = event.currentTarget.value
                      setValues((current) => ({
                        ...current,
                        [analyte.code]: nextValue,
                      }))
                    }}
                    inputMode="decimal"
                  />
                </div>
              ))}
            </div>
          </div>
        )}
        {target?.type === "reflex" && (
          <div className="mt-6 space-y-4">
            <div>
              <div className="font-medium">
                {target.rule.trigger_analyte_code} ·{" "}
                {target.rule.trigger_analyte_name}
              </div>
              <div className="mt-1 rounded-md bg-muted p-3 font-mono text-sm">
                {OPERATOR_LABELS[target.rule.trigger_operator]}{" "}
                {target.rule.trigger_value}
              </div>
            </div>
            <Input
              value={sampleValue}
              onChange={(event) => setSampleValue(event.currentTarget.value)}
              placeholder="Valeur exemple"
            />
          </div>
        )}
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <LoadingButton loading={isLoading} onClick={runPreview}>
            Tester
          </LoadingButton>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Fermer
          </Button>
        </div>
        {message && (
          <div className="mt-4 rounded-md border p-3 text-sm">
            <div className="font-medium">{message}</div>
            {result && (
              <div className="font-mono">
                Résultat: {formatPreviewResult(result, resultType)}
              </div>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}

function formatPreviewResult(
  result: string,
  resultType: FormulaResultType | null,
) {
  if (resultType === "number") return formatDecimal(result)
  if (result === "true") return "Vrai"
  if (result === "false") return "Faux"
  return result
}

function errorMessage(error: unknown) {
  const maybeError = error as { body?: { detail?: string }; message?: string }
  return (
    maybeError.body?.detail ??
    maybeError.message ??
    "Prévisualisation impossible"
  )
}
