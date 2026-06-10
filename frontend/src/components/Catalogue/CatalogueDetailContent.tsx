import { useMutation, useQueryClient } from "@tanstack/react-query"
import { RotateCcw, Save, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"

import type { CatalogDetailPublic } from "@/client"
import { CatalogService } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
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
import { AnalyteAttachments } from "./AnalyteAttachments"
import { CatalogTypeBadge } from "./CatalogTypeBadge"
import { CatalogueMetadataForm } from "./CatalogueMetadataForm"
import { PanelItems } from "./PanelItems"
import { SpecimenRequirements } from "./SpecimenRequirements"
import { type CatalogFormState, NONE } from "./types"
import { buildCatalogUpdateRequest } from "./utils"

interface CatalogueDetailContentProps {
  detail: CatalogDetailPublic
  onDelete: (id: string) => void
  onRestore: (id: string) => void
  loadCategoryOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function CatalogueDetailContent({
  detail,
  onDelete,
  onRestore,
  loadCategoryOptions,
}: CatalogueDetailContentProps) {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [form, setForm] = useState<CatalogFormState>(() =>
    formFromDetail(detail),
  )

  useEffect(() => {
    setForm(formFromDetail(detail))
  }, [detail])

  const updateMutation = useMutation({
    mutationFn: () =>
      CatalogService.updateCatalog({
        id: detail.id,
        requestBody: buildCatalogUpdateRequest(form),
      }),
    onSuccess: () => {
      showSuccessToast("Catalogue mis à jour")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["catalog"] })
    },
  })

  return (
    <div className="flex flex-col gap-4">
      <Card className="shadow-none">
        <CardHeader className="gap-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="mb-2">
                <CatalogTypeBadge type={detail.type} />
              </div>
              <CardTitle className="truncate">{detail.name}</CardTitle>
              <CardDescription>
                {detail.code} · {formatPrice(detail.price)}
              </CardDescription>
            </div>
            {canManage &&
              (detail.is_deleted ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRestore(detail.id)}
                >
                  <RotateCcw className="size-4" />
                  Restaurer
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDelete(detail.id)}
                >
                  <Trash2 className="size-4" />
                  Supprimer
                </Button>
              ))}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <CatalogueMetadataForm
            form={form}
            lockType
            onChange={setForm}
            loadCategoryOptions={loadCategoryOptions}
          />
          {canManage && (
            <Button
              className="w-full"
              onClick={() => updateMutation.mutate()}
              disabled={
                updateMutation.isPending ||
                !form.code.trim() ||
                !form.name.trim()
              }
            >
              <Save className="size-4" />
              Enregistrer les métadonnées
            </Button>
          )}
        </CardContent>
      </Card>

      {detail.type === "item" ? (
        <>
          <AnalyteAttachments detail={detail} />
          <SpecimenRequirements detail={detail} />
        </>
      ) : (
        <PanelItems detail={detail} />
      )}
    </div>
  )
}

function formFromDetail(detail: CatalogDetailPublic): CatalogFormState {
  return {
    type: detail.type,
    code: detail.code,
    name: detail.name,
    price: detail.price ?? "0.00",
    categoryId: detail.category_id ?? NONE,
    categoryLabel: detail.category_name ?? "",
    isOrderable: detail.is_orderable ?? true,
  }
}
