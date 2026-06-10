import { X } from "lucide-react"

import type { CatalogType } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ALL, type OrderableFilter, type StatusFilter } from "./types"

interface CatalogueFiltersProps {
  statusFilter: StatusFilter
  typeFilter: string
  categoryFilter: string
  categoryFilterOption: SearchSelectOption | null
  orderableFilter: OrderableFilter
  activeFilterCount: number
  search: string
  onStatusFilterChange: (value: StatusFilter) => void
  onTypeFilterChange: (value: CatalogType | typeof ALL) => void
  onCategoryFilterChange: (
    value: string,
    option: SearchSelectOption | null,
  ) => void
  onOrderableFilterChange: (value: OrderableFilter) => void
  onReset: () => void
  loadCategoryOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function CatalogueFilters({
  statusFilter,
  typeFilter,
  categoryFilter,
  categoryFilterOption,
  orderableFilter,
  activeFilterCount,
  search,
  onStatusFilterChange,
  onTypeFilterChange,
  onCategoryFilterChange,
  onOrderableFilterChange,
  onReset,
  loadCategoryOptions,
}: CatalogueFiltersProps) {
  return (
    <Card className="rounded-lg py-4 shadow-none">
      <CardContent className="flex flex-wrap items-end gap-4">
        <FilterSelect
          label="Statut"
          value={statusFilter}
          onValueChange={(value) => onStatusFilterChange(value as StatusFilter)}
          options={[
            ["active", "Actifs"],
            ["deleted", "Supprimés"],
            ["all", "Tous"],
          ]}
        />
        <FilterSelect
          label="Type"
          value={typeFilter}
          onValueChange={(value) =>
            onTypeFilterChange(value as CatalogType | typeof ALL)
          }
          options={[
            [ALL, "Tous"],
            ["item", "Tests"],
            ["panel", "Panels"],
          ]}
        />
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs text-muted-foreground">Catégorie</Label>
          <SearchSelect
            value={categoryFilter === ALL ? null : categoryFilter}
            selectedOption={categoryFilterOption}
            onValueChange={(value, option) =>
              onCategoryFilterChange(value ?? ALL, option ?? null)
            }
            loadOptions={loadCategoryOptions}
            placeholder="Toutes"
            searchPlaceholder="Rechercher une catégorie…"
            emptyMessage="Aucune catégorie"
            className="w-52"
          />
        </div>
        <FilterSelect
          label="Commandable"
          value={orderableFilter}
          onValueChange={(value) =>
            onOrderableFilterChange(value as OrderableFilter)
          }
          options={[
            ["all", "Tous"],
            ["yes", "Oui"],
            ["no", "Non"],
          ]}
        />
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

function FilterSelect({
  label,
  value,
  onValueChange,
  options,
}: {
  label: string
  value: string
  onValueChange: (value: string) => void
  options: Array<[string, string]>
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger size="sm" className="w-40">
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
