import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { ItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { usePermission } from "@/hooks/usePermission"
import DeleteItem from "../Items/DeleteItem"
import EditItem from "../Items/EditItem"

interface ItemActionsMenuProps {
  item: ItemPublic
}

export const ItemActionsMenu = ({ item }: ItemActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const canEdit = usePermission("items", "edit")
  const canDelete = usePermission("items", "delete")

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {canEdit && <EditItem item={item} onSuccess={() => setOpen(false)} />}
        {canDelete && (
          <DeleteItem id={item.id} onSuccess={() => setOpen(false)} />
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
