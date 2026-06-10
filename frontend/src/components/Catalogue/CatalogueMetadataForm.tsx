import type { CatalogType } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { type CatalogFormState, NONE } from "./types"

interface CatalogueMetadataFormProps {
  form: CatalogFormState
  lockType?: boolean
  onChange: (form: CatalogFormState) => void
  loadCategoryOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function CatalogueMetadataForm({
  form,
  lockType,
  onChange,
  loadCategoryOptions,
}: CatalogueMetadataFormProps) {
  return (
    <div className="grid gap-4 py-2">
      <div className="grid gap-4 sm:grid-cols-2">
        <div
          className={`grid gap-1.5 ${form.type === "panel" ? "sm:col-span-2" : ""}`}
        >
          <Label>Type</Label>
          <Select
            value={form.type}
            onValueChange={(value) =>
              onChange({ ...form, type: value as CatalogType })
            }
            disabled={lockType}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="item">Test</SelectItem>
              <SelectItem value="panel">Panel</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-1.5">
          <Label>Code</Label>
          <Input
            value={form.code}
            onChange={(event) =>
              onChange({
                ...form,
                code: event.currentTarget.value.toUpperCase(),
              })
            }
            placeholder="ex. GLU"
          />
        </div>
      </div>
      <div className="grid gap-1.5">
        <Label>Nom</Label>
        <Input
          value={form.name}
          onChange={(event) =>
            onChange({ ...form, name: event.currentTarget.value })
          }
          placeholder="Nom affiché dans le catalogue"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {form.type === "item" && (
          <div className="grid gap-1.5">
            <Label>Prix</Label>
            <Input
              value={form.price}
              onChange={(event) =>
                onChange({ ...form, price: event.currentTarget.value })
              }
              inputMode="decimal"
              placeholder="0.00"
            />
          </div>
        )}
        <div className="grid gap-1.5">
          <Label>Catégorie</Label>
          <SearchSelect
            value={form.categoryId === NONE ? null : form.categoryId}
            selectedOption={
              form.categoryId === NONE
                ? null
                : { value: form.categoryId, label: form.categoryLabel }
            }
            onValueChange={(value, option) =>
              onChange({
                ...form,
                categoryId: value ?? NONE,
                categoryLabel: option?.label ?? "",
              })
            }
            loadOptions={loadCategoryOptions}
            placeholder="Non classé"
            searchPlaceholder="Rechercher une catégorie…"
            emptyMessage="Aucune catégorie"
          />
        </div>
      </div>
      <div className="flex items-center justify-between rounded-lg border p-3">
        <div>
          <Label>Commandable</Label>
          <p className="text-sm text-muted-foreground">
            Disponible lors de la création des demandes.
          </p>
        </div>
        <Switch
          checked={form.isOrderable}
          onCheckedChange={(checked) =>
            onChange({ ...form, isOrderable: checked })
          }
        />
      </div>
    </div>
  )
}
