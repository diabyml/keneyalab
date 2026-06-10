import { useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"
import type { PaymentMethodPublic } from "@/client"
import { PaymentMethodsService } from "@/client"
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
import { DeleteMethodePaiementDialog } from "./DeleteMethodePaiementDialog"
import { MethodePaiementDialog } from "./MethodePaiementDialog"

interface Props {
  item: PaymentMethodPublic
}

export function MethodePaiementActionsMenu({ item }: Props) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canManage = usePermission("reference_data", "manage")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  if (!canManage) return null

  const handleRestore = async () => {
    try {
      await PaymentMethodsService.restorePaymentMethod({ id: item.id })
      showSuccessToast(`La méthode « ${item.name} » a été restaurée`)
      queryClient.invalidateQueries()
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
      <MethodePaiementDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        item={item}
      />
      <DeleteMethodePaiementDialog
        id={item.id}
        name={item.name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
