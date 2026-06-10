import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2 } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { CatalogDetailPublic } from "@/client"
import { AnalytesService, CatalogService } from "@/client"
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
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { OrderButtons } from "./OrderButtons"
import { swapOrder } from "./utils"

export function AnalyteAttachments({
  detail,
}: {
  detail: CatalogDetailPublic
}) {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [analyteId, setAnalyteId] = useState("")
  const attachedIds = useMemo(
    () => new Set((detail.analytes ?? []).map((item) => item.analyte_id)),
    [detail.analytes],
  )
  const loadAnalyteOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await AnalytesService.readAnalytes({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((analyte) => ({
        value: analyte.id,
        label: `${analyte.code} · ${analyte.name}`,
        description: analyte.data_type,
        disabled: attachedIds.has(analyte.id),
      }))
    },
    [attachedIds],
  )

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["catalog"] })
  }

  const addMutation = useMutation({
    mutationFn: () =>
      CatalogService.addCatalogAnalyte({
        id: detail.id,
        requestBody: {
          analyte_id: analyteId,
          sort_order: (detail.analytes?.length ?? 0) + 1,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Analyte attaché")
      setAnalyteId("")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  const removeMutation = useMutation({
    mutationFn: (attachmentId: string) =>
      CatalogService.removeCatalogAnalyte({ id: detail.id, attachmentId }),
    onSuccess: () => showSuccessToast("Analyte retiré"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  const reorderMutation = useMutation({
    mutationFn: (items: { id: string; sort_order: number }[]) =>
      CatalogService.reorderCatalogAnalytes({
        id: detail.id,
        requestBody: { items },
      }),
    onSuccess: () => showSuccessToast("Ordre des analytes mis à jour"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle>Analytes</CardTitle>
        <CardDescription>Résultats produits par ce test.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {canManage && (
          <div className="flex gap-2">
            <SearchSelect
              value={analyteId || null}
              onValueChange={(value) => setAnalyteId(value ?? "")}
              loadOptions={loadAnalyteOptions}
              placeholder="Sélectionner un analyte"
              searchPlaceholder="Rechercher un analyte…"
              emptyMessage="Aucun analyte"
            />
            <Button
              onClick={() => addMutation.mutate()}
              disabled={!analyteId || addMutation.isPending}
            >
              <Plus className="size-4" />
            </Button>
          </div>
        )}
        <div className="space-y-2">
          {(detail.analytes ?? []).map((item, index, rows) => (
            <div
              key={item.id}
              className="flex items-center gap-2 rounded-lg border p-2"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">
                  {item.analyte_code} · {item.analyte_name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {item.analyte_data_type}
                  {item.unit_name ? ` · ${item.unit_name}` : ""}
                </div>
              </div>
              {canManage && (
                <>
                  <OrderButtons
                    index={index}
                    length={rows.length}
                    onMove={(direction) => {
                      const next = swapOrder(rows, index, direction)
                      if (next) reorderMutation.mutate(next)
                    }}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 text-muted-foreground"
                    onClick={() => removeMutation.mutate(item.id)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </>
              )}
            </div>
          ))}
          {(detail.analytes ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground">
              Aucun analyte attaché.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
