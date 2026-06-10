import { useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"
import type { InsuranceProviderPublic } from "@/client"
import { InsuranceProvidersService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { AssureurDialog } from "./AssureurDialog"
import { DeleteAssureurDialog } from "./DeleteAssureurDialog"

interface Props {
  item: InsuranceProviderPublic
  onRestored?: () => void
}

export function AssureurActionsMenu({ item, onRestored }: Props) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canManage = usePermission("reference_data", "manage")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  if (!canManage) return null

  const handleRestore = async () => {
    try {
      await InsuranceProvidersService.restoreInsuranceProvider({ id: item.id })
      showSuccessToast(`L'assureur « ${item.name} » a été restauré`)
      queryClient.invalidateQueries({ queryKey: ["insurance-providers"] })
      onRestored?.()
    } catch (err) {
      handleError.call(showErrorToast, err as any)
    }
  }

  return (
    <>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onSelect={(e) => e.preventDefault()}
            onClick={() => {
              setEditOpen(true)
              setOpen(false)
            }}
          >
            <Pencil />
            Modifier
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          {item.is_deleted ? (
            <DropdownMenuItem
              onSelect={(e) => e.preventDefault()}
              onClick={() => {
                handleRestore()
                setOpen(false)
              }}
            >
              <RotateCcw />
              Restaurer
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem
              variant="destructive"
              onSelect={(e) => e.preventDefault()}
              onClick={() => {
                setDeleteOpen(true)
                setOpen(false)
              }}
            >
              <Trash2 />
              Supprimer
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <AssureurDialog open={editOpen} onOpenChange={setEditOpen} item={item} />
      <DeleteAssureurDialog
        id={item.id}
        name={item.name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
