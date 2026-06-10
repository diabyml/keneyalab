import type { RuleSeverity, TriggerOperator } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { SearchSelect } from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { OPERATOR_OPTIONS, SEVERITY_OPTIONS, STATUS_OPTIONS } from "./labels"

export type StatusFilter = "active" | "deleted" | "all"
export type SeverityFilter = RuleSeverity | "all"
export type OperatorFilter = TriggerOperator | "all"

interface ConsistencyFiltersProps {
  status: StatusFilter
  severity: SeverityFilter
  analyteId: string | null
  analyteOption: SearchSelectOption | null
  onStatusChange: (value: StatusFilter) => void
  onSeverityChange: (value: SeverityFilter) => void
  onAnalyteChange: (value: string | null, option?: SearchSelectOption) => void
  onReset: () => void
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
}

interface ReflexFiltersProps {
  status: StatusFilter
  operator: OperatorFilter
  triggerAnalyteId: string | null
  triggerAnalyteOption: SearchSelectOption | null
  actionCatalogId: string | null
  actionCatalogOption: SearchSelectOption | null
  onStatusChange: (value: StatusFilter) => void
  onOperatorChange: (value: OperatorFilter) => void
  onTriggerAnalyteChange: (
    value: string | null,
    option?: SearchSelectOption,
  ) => void
  onActionCatalogChange: (
    value: string | null,
    option?: SearchSelectOption,
  ) => void
  onReset: () => void
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadCatalogOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ConsistencyFilters({
  status,
  severity,
  analyteId,
  analyteOption,
  onStatusChange,
  onSeverityChange,
  onAnalyteChange,
  onReset,
  loadAnalyteOptions,
}: ConsistencyFiltersProps) {
  return (
    <div className="grid gap-3 rounded-md border bg-muted/20 p-3 md:grid-cols-[160px_180px_1fr_auto]">
      <Select
        value={status}
        onValueChange={(value) => onStatusChange(value as StatusFilter)}
      >
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select
        value={severity}
        onValueChange={(value) => onSeverityChange(value as SeverityFilter)}
      >
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SEVERITY_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <SearchSelect
        value={analyteId}
        selectedOption={analyteOption}
        onValueChange={onAnalyteChange}
        loadOptions={loadAnalyteOptions}
        placeholder="Tous les analytes"
        searchPlaceholder="Rechercher un analyte…"
      />
      <Button type="button" variant="outline" onClick={onReset}>
        Réinitialiser
      </Button>
    </div>
  )
}

export function ReflexFilters({
  status,
  operator,
  triggerAnalyteId,
  triggerAnalyteOption,
  actionCatalogId,
  actionCatalogOption,
  onStatusChange,
  onOperatorChange,
  onTriggerAnalyteChange,
  onActionCatalogChange,
  onReset,
  loadAnalyteOptions,
  loadCatalogOptions,
}: ReflexFiltersProps) {
  return (
    <div className="grid gap-3 rounded-md border bg-muted/20 p-3 lg:grid-cols-[160px_140px_1fr_1fr_auto]">
      <Select
        value={status}
        onValueChange={(value) => onStatusChange(value as StatusFilter)}
      >
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select
        value={operator}
        onValueChange={(value) => onOperatorChange(value as OperatorFilter)}
      >
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {OPERATOR_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <SearchSelect
        value={triggerAnalyteId}
        selectedOption={triggerAnalyteOption}
        onValueChange={onTriggerAnalyteChange}
        loadOptions={loadAnalyteOptions}
        placeholder="Analyte déclencheur"
        searchPlaceholder="Rechercher un analyte…"
      />
      <SearchSelect
        value={actionCatalogId}
        selectedOption={actionCatalogOption}
        onValueChange={onActionCatalogChange}
        loadOptions={loadCatalogOptions}
        placeholder="Action catalogue"
        searchPlaceholder="Rechercher dans le catalogue…"
      />
      <Button type="button" variant="outline" onClick={onReset}>
        Réinitialiser
      </Button>
    </div>
  )
}
