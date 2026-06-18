import {
  ArrowDown,
  ArrowUp,
  MoreHorizontal,
  Plus,
  Trash2,
  X,
} from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { OrderAnalyteDetailPublic } from "@/client"
import { AnalytesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function TestAnalyteActionsMenu({
  analyte,
  index,
  length,
  busy = false,
  onMove,
  onRemove,
}: {
  analyte: OrderAnalyteDetailPublic
  index: number
  length: number
  busy?: boolean
  onMove: (direction: -1 | 1) => void
  onRemove: () => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground"
          disabled={busy}
          aria-label={`Actions pour ${analyte.analyte_name}`}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem disabled={index === 0} onSelect={() => onMove(-1)}>
          <ArrowUp className="size-4" />
          Monter
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={index + 1 >= length}
          onSelect={() => onMove(1)}
        >
          <ArrowDown className="size-4" />
          Descendre
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onSelect={onRemove}>
          <Trash2 className="size-4" />
          Retirer
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function AddAnalyteControl({
  analytes,
  busy = false,
  onAdd,
}: {
  analytes: OrderAnalyteDetailPublic[]
  busy?: boolean
  onAdd: (analyteId: string) => void
}) {
  const [adding, setAdding] = useState(false)
  const activeIds = useMemo(
    () => new Set(analytes.map((analyte) => analyte.analyte_id)),
    [analytes],
  )
  const loadOptions = useCallback(
    async (search: string): Promise<SearchSelectOption[]> => {
      const response = await AnalytesService.readAnalytes({
        search: search || undefined,
        isDeleted: false,
        limit: 20,
      })
      return response.data.map((analyte) => ({
        value: analyte.id,
        label: `${analyte.code} · ${analyte.name}`,
        description: analyte.data_type,
        disabled: activeIds.has(analyte.id),
      }))
    },
    [activeIds],
  )

  if (!adding) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-8 text-muted-foreground"
        disabled={busy}
        onClick={() => setAdding(true)}
      >
        <Plus className="size-4" />
        Ajouter un analyte
      </Button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="min-w-0 flex-1">
        <SearchSelect
          value={null}
          onValueChange={(value) => {
            if (!value) return
            onAdd(value)
            setAdding(false)
          }}
          loadOptions={loadOptions}
          placeholder="Rechercher un analyte…"
          searchPlaceholder="Code ou nom de l'analyte…"
          emptyMessage="Aucun analyte disponible"
          clearable={false}
          disabled={busy}
          autoFocus
          onEscape={() => setAdding(false)}
        />
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-8"
        onClick={() => setAdding(false)}
        aria-label="Annuler l'ajout"
      >
        <X className="size-4" />
      </Button>
    </div>
  )
}

export function TestAnalyteEditor({
  analytes,
  disabled = false,
  busy = false,
  onChange,
}: {
  analytes: OrderAnalyteDetailPublic[]
  disabled?: boolean
  busy?: boolean
  onChange: (
    analyteIds: string[],
    context?: { removed?: OrderAnalyteDetailPublic },
  ) => void
}) {
  return (
    <div className="border-l border-border/70 pl-3">
      <p className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        Analytes
      </p>
      <div className="space-y-0.5">
        {analytes.map((analyte, index) => (
          <div
            key={analyte.analyte_id}
            className="group flex min-h-8 items-center gap-2 rounded-md px-2 text-xs hover:bg-muted/40"
          >
            <span className="min-w-0 flex-1">
              <span className="block truncate font-medium">
                {analyte.analyte_code} · {analyte.analyte_name}
              </span>
              <span className="block truncate text-[11px] text-muted-foreground">
                {analyte.analyte_data_type}
                {analyte.unit_name ? ` · ${analyte.unit_name}` : ""}
              </span>
            </span>
            {!disabled && (
              <TestAnalyteActionsMenu
                analyte={analyte}
                index={index}
                length={analytes.length}
                busy={busy}
                onMove={(direction) => {
                  const next = analytes.map((item) => item.analyte_id)
                  const target = index + direction
                  ;[next[index], next[target]] = [next[target], next[index]]
                  onChange(next)
                }}
                onRemove={() =>
                  onChange(
                    analytes
                      .filter((item) => item.analyte_id !== analyte.analyte_id)
                      .map((item) => item.analyte_id),
                    { removed: analyte },
                  )
                }
              />
            )}
          </div>
        ))}

        {!disabled && (
          <div className="px-2 pt-1">
            <AddAnalyteControl
              analytes={analytes}
              busy={busy}
              onAdd={(analyteId) =>
                onChange([
                  ...analytes.map((item) => item.analyte_id),
                  analyteId,
                ])
              }
            />
          </div>
        )}
      </div>
    </div>
  )
}
