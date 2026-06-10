import type { TargetGenderType, ValidationRuleDetailPublic } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"

export const ALL = "__all__"
export const NONE = "__none__"

export type ActiveFilter = "active" | "inactive" | "all"
export type SortBy = "priority" | "analyte_code" | "analyte_name" | "is_active"

export interface RuleFormState {
  analyteId: string
  analyteLabel: string
  isActive: boolean
  targetGender: TargetGenderType
  minAgeYears: string
  maxAgeYears: string
  contextId: string
  contextLabel: string
  priority: string
  absurdMin: string
  absurdMax: string
  panicMin: string
  panicMax: string
  normalMin: string
  normalMax: string
  expectedValue: string
  maxDeltaPercent: string
  isRequired: boolean
  regexPattern: string
  validationMessage: string
  allowedValues: string
  abnormalValues: string
  criticalValues: string
}

export interface SimulatorState {
  analyteId: string
  analyteLabel: string
  gender: string
  ageYears: string
  contextId: string
  contextLabel: string
  resultValue: string
  previousValue: string
}

export interface ValidationRuleFilterState {
  activeFilter: ActiveFilter
  dataTypeFilter: string
  genderFilter: string
  ageFilter: string
  analyteFilter: string
  analyteFilterOption: SearchSelectOption | null
  contextFilter: string
  contextFilterOption: SearchSelectOption | null
}

export type EditValidationRuleHandler = (
  rule: ValidationRuleDetailPublic,
) => void
