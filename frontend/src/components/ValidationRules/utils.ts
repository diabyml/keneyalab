import type { ValidationRuleCreate, ValidationRuleDetailPublic } from "@/client"
import { formatDecimal } from "@/lib/format"
import { TARGET_GENDER_LABELS } from "./labels"
import { type ActiveFilter, ALL, NONE, type RuleFormState } from "./types"

export function emptyRuleForm(): RuleFormState {
  return {
    analyteId: "",
    analyteLabel: "",
    isActive: true,
    targetGender: "all",
    minAgeYears: "",
    maxAgeYears: "",
    contextId: NONE,
    contextLabel: "",
    priority: "0",
    absurdMin: "",
    absurdMax: "",
    panicMin: "",
    panicMax: "",
    normalMin: "",
    normalMax: "",
    expectedValue: "",
    maxDeltaPercent: "",
    isRequired: false,
    regexPattern: "",
    validationMessage: "",
    allowedValues: "",
    abnormalValues: "",
    criticalValues: "",
  }
}

export function activeToBool(value: ActiveFilter): boolean | null {
  if (value === "active") return true
  if (value === "inactive") return false
  return null
}

export function nullableNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value)
}

export function nullableDecimal(value: string): string | null {
  return value.trim() === "" ? null : value.trim()
}

export function normalizeDecimalInput(value: string): string | null {
  const cleaned = value.trim().replace(/\s/g, "")
  if (!cleaned) return null
  if (cleaned.includes(",") && !cleaned.includes(".")) {
    return cleaned.replace(",", ".")
  }
  return cleaned
}

export function ruleToForm(rule: ValidationRuleDetailPublic): RuleFormState {
  return {
    analyteId: rule.analyte_id,
    analyteLabel: `${rule.analyte_code} - ${rule.analyte_name}`,
    isActive: rule.is_active ?? true,
    targetGender: rule.target_gender ?? "all",
    minAgeYears: rule.min_age_years?.toString() ?? "",
    maxAgeYears: rule.max_age_years?.toString() ?? "",
    contextId: rule.required_context_id ?? NONE,
    contextLabel: rule.required_context_name ?? "",
    priority: rule.priority?.toString() ?? "0",
    absurdMin: rule.absurd_min ?? "",
    absurdMax: rule.absurd_max ?? "",
    panicMin: rule.panic_min ?? "",
    panicMax: rule.panic_max ?? "",
    normalMin: rule.normal_min ?? "",
    normalMax: rule.normal_max ?? "",
    expectedValue: rule.expected_value ?? "",
    maxDeltaPercent: rule.max_delta_percent ?? "",
    isRequired: rule.is_required ?? false,
    regexPattern: rule.regex_pattern ?? "",
    validationMessage: rule.validation_message ?? "",
    allowedValues: valuesToText(rule.allowed_values),
    abnormalValues: valuesToText(rule.abnormal_values),
    criticalValues: valuesToText(rule.critical_values),
  }
}

export function buildPayload(form: RuleFormState): ValidationRuleCreate {
  return {
    analyte_id: form.analyteId,
    is_active: form.isActive,
    target_gender: form.targetGender,
    min_age_years: nullableNumber(form.minAgeYears),
    max_age_years: nullableNumber(form.maxAgeYears),
    required_context_id: form.contextId === NONE ? null : form.contextId,
    priority: Number(form.priority || 0),
    absurd_min: nullableDecimal(form.absurdMin),
    absurd_max: nullableDecimal(form.absurdMax),
    panic_min: nullableDecimal(form.panicMin),
    panic_max: nullableDecimal(form.panicMax),
    normal_min: nullableDecimal(form.normalMin),
    normal_max: nullableDecimal(form.normalMax),
    expected_value: nullableDecimal(form.expectedValue),
    max_delta_percent: nullableDecimal(form.maxDeltaPercent),
    is_required: form.isRequired,
    regex_pattern: form.regexPattern.trim() || null,
    validation_message: form.validationMessage.trim() || null,
    allowed_values: textToValues(form.allowedValues),
    abnormal_values: textToValues(form.abnormalValues),
    critical_values: textToValues(form.criticalValues),
  }
}

export function populationLabel(rule: ValidationRuleDetailPublic) {
  const pieces = [TARGET_GENDER_LABELS[rule.target_gender ?? "all"]]
  if (rule.min_age_years !== null || rule.max_age_years !== null) {
    pieces.push(`${rule.min_age_years ?? "0"}-${rule.max_age_years ?? "∞"} ans`)
  }
  if (rule.required_context_name) {
    pieces.push(rule.required_context_name)
  }
  return pieces.join(" · ")
}

export function ruleSummary(rule: ValidationRuleDetailPublic) {
  if (rule.analyte_data_type === "numeric") {
    const normalRange = formatBoundedRange(rule.normal_min, rule.normal_max)
    const panicRange = formatBoundedRange(rule.panic_min, rule.panic_max)
    const absurdRange = formatBoundedRange(rule.absurd_min, rule.absurd_max)

    return {
      normal: normalRange ?? "Non défini",
      unit: normalRange ? (rule.unit_name ?? "") : "",
      panic: panicRange,
      absurd: absurdRange,
    }
  }

  if (rule.analyte_data_type === "text") {
    return {
      text: `${rule.is_required ? "Obligatoire" : "Optionnel"}${
        rule.regex_pattern ? ` · Regex: ${rule.regex_pattern}` : ""
      }`,
    }
  }

  if (rule.analyte_data_type === "options") {
    return {
      text: `Autorisées: ${textList(rule.allowed_values) || "options analyte"}`,
    }
  }

  return {
    text: rule.is_required ? "Image obligatoire" : "Image optionnelle",
  }
}

function valuesToText(values: unknown): string {
  if (!Array.isArray(values)) return ""
  return values.filter((value) => typeof value === "string").join("\n")
}

function textToValues(value: string): string[] | null {
  const values = value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
  return values.length > 0 ? values : null
}

function textList(value: unknown) {
  if (!Array.isArray(value)) return ""
  return value.filter((item) => typeof item === "string").join(", ")
}

function hasBound(value: number | string | null | undefined) {
  return value !== null && value !== undefined && value !== ""
}

function formatBoundedRange(
  min: number | string | null | undefined,
  max: number | string | null | undefined,
) {
  const hasMin = hasBound(min)
  const hasMax = hasBound(max)
  if (hasMin && hasMax) return `${formatDecimal(min)} - ${formatDecimal(max)}`
  if (hasMin) return `≥ ${formatDecimal(min)}`
  if (hasMax) return `≤ ${formatDecimal(max)}`
  return null
}

export function initialFilters() {
  return {
    activeFilter: "active" as ActiveFilter,
    dataTypeFilter: ALL,
    genderFilter: ALL,
    ageFilter: "",
    analyteFilter: ALL,
    analyteFilterOption: null,
    contextFilter: ALL,
    contextFilterOption: null,
  }
}
