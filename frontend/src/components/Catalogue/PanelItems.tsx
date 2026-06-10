import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2 } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import type { CatalogDetailPublic } from "@/client"
import { CatalogService } from "@/client"
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
import { formatPrice } from "@/lib/format"
import { handleError } from "@/utils"
import { OrderButtons } from "./OrderButtons"
import { swapOrder } from "./utils"

export function PanelItems({ detail }: { detail: CatalogDetailPublic }) {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [testId, setTestId] = useState("")
  const attachedIds = useMemo(
    () => new Set((detail.panel_items ?? []).map((item) => item.test_id)),
    [detail.panel_items],
  )
  const loadPanelTestOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await CatalogService.readCatalog({
        search: query || undefined,
        limit: 20,
        type: "item",
        includeDeleted: false,
        sortBy: "code",
      })
      return response.data.map((test) => ({
        value: test.id,
        label: `${test.code} · ${test.name}`,
        description: formatPrice(test.price),
        disabled: attachedIds.has(test.id),
      }))
    },
    [attachedIds],
  )

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["catalog"] })
  }

  const addMutation = useMutation({
    mutationFn: () =>
      CatalogService.addCatalogPanelItem({
        id: detail.id,
        requestBody: {
          test_id: testId,
          sort_order: (detail.panel_items?.length ?? 0) + 1,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Test ajouté au panel")
      setTestId("")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  const removeMutation = useMutation({
    mutationFn: (panelItemId: string) =>
      CatalogService.removeCatalogPanelItem({ id: detail.id, panelItemId }),
    onSuccess: () => showSuccessToast("Test retiré du panel"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  const reorderMutation = useMutation({
    mutationFn: (items: { id: string; sort_order: number }[]) =>
      CatalogService.reorderCatalogPanelItems({
        id: detail.id,
        requestBody: { items },
      }),
    onSuccess: () => showSuccessToast("Ordre du panel mis à jour"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle>Tests du panel</CardTitle>
        <CardDescription>Composition commandée avec ce panel.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {canManage && (
          <div className="flex gap-2">
            <SearchSelect
              value={testId || null}
              onValueChange={(value) => setTestId(value ?? "")}
              loadOptions={loadPanelTestOptions}
              placeholder="Sélectionner un test"
              searchPlaceholder="Rechercher un test…"
              emptyMessage="Aucun test"
            />
            <Button
              onClick={() => addMutation.mutate()}
              disabled={!testId || addMutation.isPending}
            >
              <Plus className="size-4" />
            </Button>
          </div>
        )}
        <div className="space-y-2">
          {(detail.panel_items ?? []).map((item, index, rows) => (
            <div
              key={item.id}
              className="flex items-center gap-2 rounded-lg border p-2"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">
                  {item.test_code} · {item.test_name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatPrice(item.test_price)}
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
          {(detail.panel_items ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground">
              Aucun test dans ce panel.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
