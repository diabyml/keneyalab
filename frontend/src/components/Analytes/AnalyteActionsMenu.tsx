import { useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"

import type { AnalytePublic } from "@/client"
import { AnalytesService } from "@/client"
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
import { AnalyteDialog } from "./AnalyteDialog"
import { DeleteAnalyteDialog } from "./DeleteAnalyteDialog"

interface AnalyteActionsMenuProps {
  analyte: AnalytePublic
}

export function AnalyteActionsMenu({ analyte }: AnalyteActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canManage = usePermission("catalog", "manage")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const isDeleted = analyte.is_deleted

  if (!canManage) return null

  const handleRestore = async () => {
    try {
      await AnalytesService.restoreAnalyte({ id: analyte.id })
      showSuccessToast(`L'analyte « ${analyte.name} » a été restauré`)
      queryClient.invalidateQueries({ queryKey: ["analytes"] })
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

      <AnalyteDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        analyte={analyte}
      />

      <DeleteAnalyteDialog
        id={analyte.id}
        name={analyte.name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
