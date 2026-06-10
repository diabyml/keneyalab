import { useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"

import type { CategoryPublic } from "@/client"
import { CategoriesService } from "@/client"
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
import { CategoryDialog } from "./CategoryDialog"
import { DeleteCategoryDialog } from "./DeleteCategoryDialog"

interface CategoryActionsMenuProps {
  category: CategoryPublic
}

export function CategoryActionsMenu({ category }: CategoryActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canManage = usePermission("catalog", "manage")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const isDeleted = category.is_deleted

  if (!canManage) return null

  const handleRestore = async () => {
    try {
      await CategoriesService.restoreCategory({ id: category.id })
      showSuccessToast(`La catégorie « ${category.name} » a été restaurée`)
      queryClient.invalidateQueries({ queryKey: ["categories"] })
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

      <CategoryDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        category={category}
        nextSortOrder={category.sort_order ?? 0}
      />

      <DeleteCategoryDialog
        id={category.id}
        name={category.name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
