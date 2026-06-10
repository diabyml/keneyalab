import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Save } from "lucide-react"
import { useEffect, useState } from "react"

import type { CatalogType } from "@/client"
import { CatalogService } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { CatalogueMetadataForm } from "./CatalogueMetadataForm"
import type { CatalogFormState } from "./types"
import {
  buildCatalogRequest,
  catalogTypeLabel,
  emptyCatalogForm,
} from "./utils"

interface CatalogueDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  type: CatalogType
  onCreated: (id: string) => void
  loadCategoryOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function CatalogueDialog({
  open,
  onOpenChange,
  type,
  onCreated,
  loadCategoryOptions,
}: CatalogueDialogProps) {
  const canManage = usePermission("catalog", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [form, setForm] = useState<CatalogFormState>(emptyCatalogForm(type))

  useEffect(() => {
    if (open) setForm(emptyCatalogForm(type))
  }, [open, type])

  const mutation = useMutation({
    mutationFn: () =>
      CatalogService.createCatalog({ requestBody: buildCatalogRequest(form) }),
    onSuccess: (created) => {
      showSuccessToast(`${catalogTypeLabel(type)} catalogue créé`)
      onCreated(created.id)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["catalog"] })
    },
  })

  if (!canManage) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>
            Ajouter un {catalogTypeLabel(type).toLowerCase()}
          </DialogTitle>
          <DialogDescription>
            Créez d'abord l'entrée catalogue, puis ajoutez les analytes,
            prélèvements ou tests depuis le détail.
          </DialogDescription>
        </DialogHeader>
        <CatalogueMetadataForm
          form={form}
          lockType
          onChange={setForm}
          loadCategoryOptions={loadCategoryOptions}
        />
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Annuler
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              mutation.isPending || !form.code.trim() || !form.name.trim()
            }
          >
            <Save className="size-4" />
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
