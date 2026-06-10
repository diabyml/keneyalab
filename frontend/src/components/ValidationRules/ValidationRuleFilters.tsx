import { X } from "lucide-react"

import type { TargetGenderType } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { type ActiveFilter, ALL } from "./types"

interface ValidationRuleFiltersProps {
  activeFilter: ActiveFilter
  dataTypeFilter: string
  genderFilter: string
  ageFilter: string
  analyteFilter: string
  analyteFilterOption: SearchSelectOption | null
  contextFilter: string
  contextFilterOption: SearchSelectOption | null
  activeFilterCount: number
  search: string
  onActiveFilterChange: (value: ActiveFilter) => void
  onDataTypeFilterChange: (value: string) => void
  onGenderFilterChange: (value: TargetGenderType | typeof ALL) => void
  onAgeFilterChange: (value: string) => void
  onAnalyteFilterChange: (
    value: string,
    option: SearchSelectOption | null,
  ) => void
  onContextFilterChange: (
    value: string,
    option: SearchSelectOption | null,
  ) => void
  onReset: () => void
  loadAnalyteOptions: (query: string) => Promise<SearchSelectOption[]>
  loadContextOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function ValidationRuleFilters({
  activeFilter,
  dataTypeFilter,
  genderFilter,
  ageFilter,
  analyteFilter,
  analyteFilterOption,
  contextFilter,
  contextFilterOption,
  activeFilterCount,
  search,
  onActiveFilterChange,
  onDataTypeFilterChange,
  onGenderFilterChange,
  onAgeFilterChange,
  onAnalyteFilterChange,
  onContextFilterChange,
  onReset,
  loadAnalyteOptions,
  loadContextOptions,
}: ValidationRuleFiltersProps) {
  return (
    <Card className="rounded-lg py-4 shadow-none">
      <CardContent className="flex flex-wrap items-end gap-4">
        <FilterSelect
          label="Statut"
          value={activeFilter}
          onValueChange={(value) => onActiveFilterChange(value as ActiveFilter)}
          options={[
            ["active", "Actives"],
            ["inactive", "Inactives"],
            ["all", "Toutes"],
          ]}
        />
        <FilterSelect
          label="Type"
          value={dataTypeFilter}
          onValueChange={onDataTypeFilterChange}
          options={[
            [ALL, "Tous"],
            ["numeric", "Numérique"],
            ["text", "Texte"],
            ["options", "Options"],
            ["image", "Image"],
          ]}
        />
        <FilterSelect
          label="Genre"
          value={genderFilter}
          onValueChange={(value) =>
            onGenderFilterChange(value as TargetGenderType | typeof ALL)
          }
          options={[
            [ALL, "Tous"],
            ["male", "Homme"],
            ["female", "Femme"],
            ["all", "Règle tous genres"],
          ]}
        />
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs text-muted-foreground">Âge</Label>
          <Input
            type="number"
            min="0"
            value={ageFilter}
            onChange={(event) => onAgeFilterChange(event.currentTarget.value)}
            className="h-8 w-28"
            placeholder="Années"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs text-muted-foreground">Analyte</Label>
          <SearchSelect
            value={analyteFilter === ALL ? null : analyteFilter}
            selectedOption={analyteFilterOption}
            onValueChange={(value, option) =>
              onAnalyteFilterChange(value ?? ALL, option ?? null)
            }
            loadOptions={loadAnalyteOptions}
            placeholder="Tous"
            searchPlaceholder="Rechercher un analyte…"
            emptyMessage="Aucun analyte"
            className="w-64"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs text-muted-foreground">Contexte</Label>
          <SearchSelect
            value={contextFilter === ALL ? null : contextFilter}
            selectedOption={contextFilterOption}
            onValueChange={(value, option) =>
              onContextFilterChange(value ?? ALL, option ?? null)
            }
            loadOptions={loadContextOptions}
            placeholder="Tous"
            searchPlaceholder="Rechercher un contexte…"
            emptyMessage="Aucun contexte"
            className="w-52"
          />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          disabled={activeFilterCount === 0 && search.trim() === ""}
          className="text-muted-foreground"
        >
          <X className="size-4" />
          Réinitialiser
        </Button>
      </CardContent>
    </Card>
  )
}

export function FilterSelect({
  label,
  value,
  onValueChange,
  options,
  triggerClassName = "w-44",
}: {
  label: string
  value: string
  onValueChange: (value: string) => void
  options: Array<[string, string]>
  triggerClassName?: string
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger size="sm" className={triggerClassName}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map(([optionValue, optionLabel]) => (
            <SelectItem key={optionValue} value={optionValue}>
              {optionLabel}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
