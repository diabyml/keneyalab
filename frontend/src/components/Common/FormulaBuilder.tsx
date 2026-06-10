import { Calculator, CheckCircle2, Plus, XCircle } from "lucide-react"
import { useMemo, useState } from "react"

import type {
  FormulaPreviewResponse,
  FormulaReferencePublic,
  FormulaResultType,
} from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import { formatDecimal } from "@/lib/format"

interface FormulaBuilderProps {
  value: string
  onChange: (value: string) => void
  expectedResultType: FormulaResultType
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  previewFormula: (
    formula: string,
    values: Record<string, string>,
  ) => Promise<FormulaPreviewResponse>
  placeholder?: string
  disabled?: boolean
}

const REFERENCE_RE = /\{([A-Za-z0-9_.-]+)\}/g
const SUPPORTED_HELP = [
  "+",
  "-",
  "*",
  "/",
  "%",
  "**",
  ">",
  ">=",
  "<",
  "<=",
  "==",
  "!=",
  "and",
  "or",
  "not",
  "abs",
  "min",
  "max",
  "round",
]

export function FormulaBuilder({
  value,
  onChange,
  expectedResultType,
  loadAnalyteOptions,
  previewFormula,
  placeholder = "{GLU} / {CREAT}",
  disabled = false,
}: FormulaBuilderProps) {
  const [insertValue, setInsertValue] = useState<string | null>(null)
  const [sampleValues, setSampleValues] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState<FormulaPreviewResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)

  const references = useMemo(() => extractReferences(value), [value])

  const insertReference = (
    _selected: string | null,
    option?: SearchSelectOption,
  ) => {
    if (!option?.description) return
    const code = option.description.split(" · ")[0]
    onChange(`${value}${value.trim() ? " " : ""}{${code}}`)
    setInsertValue(null)
  }

  const runPreview = async () => {
    setIsPreviewing(true)
    setPreview(null)
    setError(null)
    try {
      const response = await previewFormula(value, sampleValues)
      setPreview(response)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setIsPreviewing(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-2">
        <Textarea
          value={value}
          onChange={(event) => {
            onChange(event.currentTarget.value)
            setPreview(null)
            setError(null)
          }}
          placeholder={placeholder}
          rows={4}
          disabled={disabled}
          className="font-mono text-sm"
        />
        <div className="flex flex-wrap gap-1.5">
          {SUPPORTED_HELP.map((item) => (
            <Badge key={item} variant="outline" className="font-mono">
              {item}
            </Badge>
          ))}
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
        <SearchSelect
          value={insertValue}
          onValueChange={insertReference}
          loadOptions={loadAnalyteOptions}
          placeholder="Insérer un analyte"
          searchPlaceholder="Rechercher un analyte…"
          emptyMessage="Aucun analyte"
          disabled={disabled}
        />
        <Button
          type="button"
          variant="outline"
          disabled
          className="hidden sm:flex"
        >
          <Plus className="size-4" />
          Référence
        </Button>
      </div>

      {references.length > 0 && (
        <div className="space-y-2 rounded-md border bg-muted/20 p-3">
          <div className="flex flex-wrap gap-1.5">
            {references.map((code) => (
              <Badge key={code} variant="secondary" className="font-mono">
                {code}
              </Badge>
            ))}
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {references.map((code) => (
              <div key={code} className="grid gap-1">
                <label
                  htmlFor={`formula-sample-${code}`}
                  className="text-xs font-medium text-muted-foreground"
                >
                  Valeur exemple {code}
                </label>
                <Input
                  id={`formula-sample-${code}`}
                  value={sampleValues[code] ?? ""}
                  onChange={(event) => {
                    const nextValue = event.currentTarget.value
                    setSampleValues((current) => ({
                      ...current,
                      [code]: nextValue,
                    }))
                  }}
                  inputMode="decimal"
                  placeholder="0"
                  disabled={disabled}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <LoadingButton
          type="button"
          variant="outline"
          loading={isPreviewing}
          disabled={!value.trim() || disabled}
          onClick={runPreview}
        >
          <Calculator className="size-4" />
          Tester
        </LoadingButton>
        <span className="text-sm text-muted-foreground">
          Résultat attendu:{" "}
          {expectedResultType === "number" ? "numérique" : "vrai / faux"}
        </span>
      </div>

      {(preview || error) && (
        <div className="rounded-md border p-3 text-sm">
          {preview ? (
            <div className="flex items-start gap-2 text-emerald-700">
              <CheckCircle2 className="mt-0.5 size-4" />
              <div>
                <div className="font-medium">{preview.message}</div>
                {preview.result && (
                  <div className="font-mono text-foreground">
                    Résultat: {formatFormulaResult(preview)}
                  </div>
                )}
                {preview.references && preview.references.length > 0 && (
                  <div className="mt-1 text-muted-foreground">
                    {referenceNames(preview.references)}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-2 text-destructive">
              <XCircle className="mt-0.5 size-4" />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function extractReferences(formula: string) {
  const matches = [...formula.matchAll(REFERENCE_RE)].map((match) =>
    match[1].trim().toUpperCase(),
  )
  return [...new Set(matches)].filter(Boolean)
}

function referenceNames(references: FormulaReferencePublic[]) {
  return references
    .map((reference) => `${reference.code} · ${reference.name}`)
    .join(", ")
}

function formatFormulaResult(preview: FormulaPreviewResponse) {
  if (preview.result_type === "number") return formatDecimal(preview.result)
  return preview.result
}

function errorMessage(error: unknown) {
  const maybeError = error as { body?: { detail?: string }; message?: string }
  return maybeError.body?.detail ?? maybeError.message ?? "Formule invalide"
}
