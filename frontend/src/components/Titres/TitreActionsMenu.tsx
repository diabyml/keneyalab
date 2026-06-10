import { useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"

import type { TitlePublic } from "@/client"
import { TitlesService } from "@/client"
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
import { DeleteTitreDialog } from "./DeleteTitreDialog"
import { TitreDialog } from "./TitreDialog"

interface TitreActionsMenuProps {
  title: TitlePublic
}

export function TitreActionsMenu({ title }: TitreActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canManage = usePermission("reference_data", "manage")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const isDeleted = title.is_deleted

  if (!canManage) return null

  const handleRestore = async () => {
    try {
      await TitlesService.restoreTitle({ id: title.id })
      showSuccessToast(`Le titre « ${title.name} » a été restauré`)
      queryClient.invalidateQueries()
    } catch (err) {
      handleError.call(showErrorToast, err as Parameters<typeof handleError>[0])
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
          {isDeleted ? (
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

      <TitreDialog open={editOpen} onOpenChange={setEditOpen} title={title} />

      <DeleteTitreDialog
        id={title.id}
        name={title.name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
