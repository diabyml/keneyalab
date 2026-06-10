import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2 } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { CatalogDetailPublic } from "@/client"
import { CatalogService, SpecimenTypesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { formatDecimal } from "@/lib/format"
import { handleError } from "@/utils"
import type { SpecimenFormState } from "./types"

export function SpecimenRequirements({
  detail,
}: {
  detail: CatalogDetailPublic
}) {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [form, setForm] = useState<SpecimenFormState>({
    specimenTypeId: "",
    volumeMl: "",
    instructions: "",
  })
  const attachedIds = useMemo(
    () =>
      new Set(
        (detail.specimen_requirements ?? []).map(
          (item) => item.specimen_type_id,
        ),
      ),
    [detail.specimen_requirements],
  )
  const loadSpecimenTypeOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await SpecimenTypesService.readSpecimenTypes({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((specimenType) => ({
        value: specimenType.id,
        label: specimenType.name,
        description: specimenType.description ?? undefined,
        disabled: attachedIds.has(specimenType.id),
      }))
    },
    [attachedIds],
  )

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["catalog"] })
  }

  const upsertMutation = useMutation({
    mutationFn: (payload: SpecimenFormState) =>
      CatalogService.upsertCatalogSpecimenRequirement({
        id: detail.id,
        specimenTypeId: payload.specimenTypeId,
        requestBody: {
          volume_ml: payload.volumeMl.trim() || null,
          instructions: payload.instructions.trim() || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Exigence de prélèvement enregistrée")
      setForm({ specimenTypeId: "", volumeMl: "", instructions: "" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  const removeMutation = useMutation({
    mutationFn: (specimenTypeId: string) =>
      CatalogService.removeCatalogSpecimenRequirement({
        id: detail.id,
        specimenTypeId,
      }),
    onSuccess: () => showSuccessToast("Exigence de prélèvement retirée"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle>Prélèvements</CardTitle>
        <CardDescription>
          Types, volume et instructions de collecte.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {canManage && (
          <div className="grid gap-3">
            <SearchSelect
              value={form.specimenTypeId || null}
              onValueChange={(value) =>
                setForm({ ...form, specimenTypeId: value ?? "" })
              }
              loadOptions={loadSpecimenTypeOptions}
              placeholder="Type de prélèvement"
              searchPlaceholder="Rechercher un type…"
              emptyMessage="Aucun type de prélèvement"
            />
            <Input
              type="number"
              value={form.volumeMl}
              onChange={(event) =>
                setForm({ ...form, volumeMl: event.currentTarget.value })
              }
              inputMode="decimal"
              min="0"
              step="0.01"
              placeholder="Volume en ml"
            />
            <Textarea
              value={form.instructions}
              onChange={(event) =>
                setForm({ ...form, instructions: event.currentTarget.value })
              }
              placeholder="Instructions de prélèvement"
            />
            <Button
              onClick={() => upsertMutation.mutate(form)}
              disabled={!form.specimenTypeId || upsertMutation.isPending}
            >
              <Plus className="size-4" />
              Ajouter l'exigence
            </Button>
          </div>
        )}
        <div className="space-y-2">
          {(detail.specimen_requirements ?? []).map((item) => (
            <div
              key={item.specimen_type_id}
              className="flex items-start gap-2 rounded-lg border p-2"
            >
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">
                  {item.specimen_type_name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {item.volume_ml
                    ? `${formatDecimal(item.volume_ml)} ml`
                    : "Volume non défini"}
                </div>
                {item.instructions && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.instructions}
                  </p>
                )}
              </div>
              {canManage && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground"
                  onClick={() => removeMutation.mutate(item.specimen_type_id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              )}
            </div>
          ))}
          {(detail.specimen_requirements ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground">
              Aucun prélèvement défini.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
